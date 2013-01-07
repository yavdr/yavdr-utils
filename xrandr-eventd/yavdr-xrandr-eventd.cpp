/* See LICENSE for copyright and license details
 * srandrd - simple randr daemon
 */
#include <stdio.h>
#include <string.h>
#include <stdarg.h>
#include <stdlib.h>
#include <signal.h>
#include <unistd.h>
#include <sys/wait.h>
#include <fcntl.h>
#include <X11/Xlib.h>
#include <X11/extensions/Xrandr.h>
#include <map>
#include <errno.h>
#include <getopt.h>
#include <syslog.h>

#define no_argument 0
#define required_argument 1
#define optional_argument 2
#define MAX_DEV 100

static std::map<RROutput, XRROutputInfo *> outputs;
static std::map<RROutput, XRROutputInfo *> connected_outputs;
static std::map<RROutput, XRROutputInfo *> disconnected_outputs;
static std::map<RROutput, bool> lastConnectionState; // false if crtc is disconnected

static char *onScript = NULL;
static char *offScript = NULL;
static char *changeScript = NULL;

static unsigned long lastHandledEvent = -1l;

static void xerror(const char *format, ...) {
	va_list args;
	va_start(args, format);
	vfprintf(stderr, format, args);
	va_end(args);
	exit(EXIT_FAILURE);
}

static int error_handler(void) {
	exit(EXIT_FAILURE);
}

static Status crtc_enable(Display *dpy, XRRScreenResources *res, RROutput outputId, RRCrtc crtcId, RRMode mode, int x,
		int y) {

	RROutput *rr_outputs = &outputId; //(RROutput *) calloc(1, sizeof(RROutput));

	return XRRSetCrtcConfig(dpy, res, crtcId, CurrentTime, x, y, mode, RR_Rotate_0, rr_outputs, 1);
}

Status crtc_disable(Display *dpy, XRRScreenResources *res, RRCrtc crtcId) {
	return XRRSetCrtcConfig(dpy, res, crtcId, CurrentTime, 0, 0, None, RR_Rotate_0, NULL, 0);
}

void get_outputs(Display *dpy, XRRScreenResources *res) {
	XRROutputInfo *oi = NULL;

	// remove old entry
	for (std::map<RROutput, XRROutputInfo *>::iterator it = outputs.begin(); it != outputs.end(); it++) {
		if (disconnected_outputs.count((*it).first) == 0) { // not in disconnected
			XRRFreeOutputInfo((*it).second);
		}
	}
	outputs.clear();
	connected_outputs.clear();

	for (int i = 0; i < res->noutput; i++) {
		if ((oi = XRRGetOutputInfo(dpy, res, res->outputs[i])) != NULL) {
			RROutput outputId = res->outputs[i];
			if (outputs.count(outputId) == 0) {
				outputs[outputId] = oi;

#ifdef DEBUG
				printf("\tid: %lu: name: %s, connection: %i, crtc: %lu crtcs:", outputId, oi->name, oi->connection,
						oi->crtc);
				for (int j = 0; j < oi->ncrtc; j++) {
					printf(" %lu", oi->crtcs[j]);
				}
				printf("\n");
#endif

			}
		}
	}
}

void scan(Display *dpy, XRRScreenResources *res) {
	XRROutputInfo *oi = NULL;
	XRRCrtcInfo *ci = NULL;

	get_outputs(dpy, res);

	for (int i = 0; i < res->noutput; i++) {
		if ((oi = outputs[res->outputs[i]]) != NULL) {
			RROutput outputId = res->outputs[i];
			if (oi->connection == 0) { // output is connected
				connected_outputs[outputId] = oi;

				if (oi->crtc != 0) { // crtc is enabled
					RRCrtc crtcId = oi->crtc;

					if (/*available_crtcs.count(crtcId) == 0 && */(ci = XRRGetCrtcInfo(dpy, res, crtcId)) != NULL) {
						//available_crtcs[crtcId] = ci;
						lastConnectionState[outputId] = false;

#ifdef DEBUG
						printf("\tavailable crtcs %lu: x: %i, y: %i, width: %i, height: %i outputs:", crtcId, ci->x,
								ci->y, ci->width, ci->height);
						for (int j = 0; j < ci->noutput; j++) {
							printf(" %lu", ci->outputs[j]);
						}
						printf("\n");
#endif

						if (ci->mode != 0 && ci->width != 0
								&& ci->height != 0 /*&& connected_crtcs.count(crtcId) == 0*/) { // we have valid data -> crtc is connected
								//connected_crtcs[crtcId] = ci;

							syslog(LOG_INFO, "crtc %lu is connected", crtcId);
						}

						XRRFreeCrtcInfo(ci);
					}
				} else { // output ist connected but crtc ist disabled
					for (int j = 0; j < oi->ncrtc; j++) {
						RRCrtc crtcId = oi->crtcs[j];
						if ((ci = XRRGetCrtcInfo(dpy, res, crtcId)) != NULL && ci->noutput == 0) {
//							for (int k = 0; k < ci->npossible; k++) {
//								if (outputId == ci->possible[k]) { // found matching output -> activate crtc

							crtc_enable(dpy, res, outputId, crtcId, res->modes[oi->npreferred - 1].id, 0, 0);

							//if (available_crtcs.count(crtcId) == 0) {
							//	available_crtcs[crtcId] = ci;
							lastConnectionState[outputId] = false;

#ifdef DEBUG
							printf("\tavailable crtcs %lu: x: %i, y: %i, width: %i, height: %i outputs:", crtcId, ci->x,
									ci->y, ci->width, ci->height);
							for (int j = 0; j < ci->noutput; j++) {
								printf(" %lu", ci->outputs[j]);
							}
							printf("\n");
#endif

							if (ci->mode != 0 && ci->width != 0 && ci->height != 0/*
							 && connected_crtcs.count(crtcId) == 0*/) { // wie have valid data -> crtc is connected

							//connected_crtcs[crtcId] = ci;

								printf("\tcrtc %lu is connected\n", crtcId);
							}

							XRRFreeCrtcInfo(ci);
						}
					}
				}

			} else {
				if (oi->crtc != 0) { // output disconnected but crtc enables
					crtc_disable(dpy, res, oi->crtc);
				}
			}
		}
	}
}

char* join_strings(const char* strings[], const char* seperator, int count) {
	char* str = NULL; /* Pointer to the joined strings  */
	size_t total_length = 0; /* Total length of joined strings */
	int i = 0; /* Loop counter                   */

	/* Find total length of joined strings */
	for (i = 0; i < count; i++)
		total_length += strlen(strings[i]);
	total_length++; /* For joined string terminator */
	total_length += strlen(seperator) * (count - 1); // for seperators

	str = (char*) malloc(total_length); /* Allocate memory for joined strings */
	str[0] = '\0'; /* Empty string we can append to      */

	/* Append all the strings */
	for (i = 0; i < count; i++) {
		strcat(str, strings[i]);
		if (i < (count - 1))
			strcat(str, seperator);
	}

	return str;
}
void handleChanges(unsigned long currentEvent, bool init) {
	if (currentEvent != lastHandledEvent) {
		bool callScript = false;

#ifdef DEBUG
		printf("\tstart - connected crtc: %lu, disconnected crtc: %lu\n", connected_outputs.size(),
				disconnected_outputs.size());
#endif

		for (std::map<RROutput, XRROutputInfo *>::iterator it = connected_outputs.begin();
				it != connected_outputs.end(); it++) {
			XRROutputInfo *oi = (*it).second;

			if (oi->connection == 0) {
				syslog(LOG_INFO, "%lu: %s is connected\n", (*it).first, oi->name);
				if (onScript != NULL && !init) {
					char *cmd;
					if (asprintf(&cmd, "%s %s", onScript, oi->name)) {
						if (system(cmd) < 0) {
							syslog(LOG_WARNING, "error: %s system\n", strerror(errno));
						}
						free(cmd);
					}
				}
			}

#ifdef DEBUG
			for (int i = 0; i < ci->noutput; i++) {
				RROutput oId = ci->outputs[i];
				if (outputs[oId]->connection == 0) {
					printf("%lu: %s is connected\n", (*it).first, outputs[oId]->name);
				}
			}
#endif

			if (!lastConnectionState[(*it).first]) {
				callScript = true;
			}
			lastConnectionState[(*it).first] = true;
		}

		for (std::map<RROutput, XRROutputInfo *>::iterator it = disconnected_outputs.begin();
				it != disconnected_outputs.end(); it++) {
			XRROutputInfo *oi = (*it).second;

			if (oi->connection == 1) {
				syslog(LOG_INFO, "%lu: %s is disconnected\n", (*it).first, oi->name);
				if (offScript != NULL && !init) {
					char *cmd;
					if (asprintf(&cmd, "%s %s", offScript, oi->name)) {
						if (system(cmd) < 0) {
							syslog(LOG_WARNING, "error: %s system\n", strerror(errno));
						}
						free(cmd);
					}
				}
			}

#ifdef DEBUG
			for (int i = 0; i < ci->noutput; i++) {
				RROutput oId = ci->outputs[i];
				if (outputs[oId]->connection == 1) {
					printf("%lu: %s is disconnected\n", (*it).first, outputs[oId]->name);
				}
			}
#endif

			disconnected_outputs.erase((*it).first);

			if (lastConnectionState[(*it).first]) {
				callScript = true;
			}
			lastConnectionState[(*it).first] = false;

			XRRFreeOutputInfo(oi);
		}

		lastHandledEvent = currentEvent;

#ifdef DEBUG
		printf("\tend   - connected crtc: %lu, disconnected crtc: %lu\n", connected_outputs.size(),
				disconnected_outputs.size());
#endif

		if (callScript && changeScript != NULL) {
#ifdef DEBUG
			printf("!!! We have to update X11 !!!\n");
#endif
			const char *argv[MAX_DEV];
			int i = 0;

			argv[i++] = changeScript;
			if (init) {
				argv[i++] = "-i";
			}

			for (std::map<RROutput, XRROutputInfo *>::iterator it = connected_outputs.begin();
					it != connected_outputs.end() && i < MAX_DEV - 1; it++, i++) {
				XRROutputInfo *oi = (*it).second;
				argv[i] = oi->name;
			}

			if (system(join_strings(argv, " ", i)) < 0) {
				syslog(LOG_WARNING, "error: %s system\n", strerror(errno));
			}
		}

	}
}

void usage() {
	printf("Usage: %s: ", NAME);
	printf(" [-h|--help|-?]");
	printf(" [--version]");
	printf(" [-d displayname | --display=DISPLAY]");
	printf(" [-s EXECUTABLE | --script=EXECUTABLE]");
	printf(" [-o EXECUTABLE | --on=EXECUTABLE]");
	printf(" [-f EXECUTABLE | --off=EXECUTABLE]");
	printf("\n");
}

int main(int argc, char **argv) {

	XEvent event;
	Display *dpy;
	uid_t uid;
	XRRScreenConfiguration *sc = NULL;
	int randrEventBase;
	int error_base;

	char *display = NULL;

	const struct option longopts[] = { { "version", no_argument, 0, 0 }, { "help", no_argument, 0, 'h' }, { "script",
			required_argument, 0, 's' }, { "on", required_argument, 0, 'o' }, { "off", required_argument, 0, 'f' }, { "display", required_argument, 0, 'd' }, { 0,
			0, 0, 0 }, };

	int index;
	int c = 0;


	//turn off getopt error message
	opterr = 1;

	if (argc > 1) {
		while (1) {
			c = getopt_long(argc, argv, "s:o:f:d:vh?", longopts, &index);
			if (c == -1)
				break;

			switch (c) {
			case 'h':
			case '?':
				usage();
				exit(0);

			case 'v':
				printf("%s %s\n", NAME, VERSION);
				exit(0);

			case 's':
				if (access(optarg, F_OK | X_OK) == 0) {
					changeScript = optarg;
				} else {
					syslog(LOG_ERR, "%s is not executable!", optarg);
					printf("%s is not executable!\n", optarg);
					exit(-1);
				}

				break;

			case 'o':
				if (access(optarg, F_OK | X_OK) == 0) {
					onScript = optarg;
				} else {
					syslog(LOG_ERR, "%s is not executable!", optarg);
					printf("%s is not executable!\n", optarg);
					exit(-1);
				}
				break;

			case 'f':
				if (access(optarg, F_OK | X_OK) == 0) {
					offScript = optarg;
				} else {
					syslog(LOG_ERR, "%s is not executable!", optarg);
					printf("%s is not executable!\n", optarg);
					exit(-1);
				}

				break;

			case 'd':
				display = optarg;
				break;

			default:
				usage();
				exit(0);
			}
		}
	}

	if (((uid = getuid()) == 0) || uid != geteuid())
		xerror("%s may not run as root\n", NAME);

	if ((dpy = XOpenDisplay(display)) == NULL)
		xerror("Cannot open display\n");
	XRRSelectInput(dpy, DefaultRootWindow(dpy),
			RRScreenChangeNotifyMask | RRCrtcChangeNotifyMask | RROutputChangeNotifyMask | RROutputPropertyNotifyMask);
	XSync(dpy, False);
	XSetIOErrorHandler((XIOErrorHandler) error_handler);
	XRRQueryExtension(dpy, &randrEventBase, &error_base);
	XRRScreenResources *res = XRRGetScreenResources(dpy, DefaultRootWindow(dpy));

#ifdef DEBUG
	printf("crtcs:\n");
	for (int i = 0; i < res->ncrtc; i++) {
		printf("\t%lu\n", res->crtcs[i]);
	}
	printf("\noutputs:\n");
	for (int i = 0; i < res->noutput; i++) {
		printf("\t%lu\n", res->outputs[i]);
	}
	printf("\nmodes:\n");
	for (int i = 0; i < res->nmode; i++) {
		printf("\tid: %lu, width: %i, height: %i, name: %s\n", res->modes[i].id, res->modes[i].width,
				res->modes[i].height, res->modes[i].name);
	}
#endif

	// query ScreenInfo to be sure because of NVidia
	sc = XRRGetScreenInfo(dpy, DefaultRootWindow(dpy));
	if (sc)
		XRRFreeScreenConfigInfo(sc);

	XRROutputInfo *oi = NULL;
	XRRCrtcInfo *ci = NULL;

	scan(dpy, res);

	handleChanges(0, true);

#ifdef DEBUG

	for (int i = 0; i < res->ncrtc; i++) {
		if ((ci = XRRGetCrtcInfo(dpy, res, res->crtcs[i])) != NULL) {
			RRCrtc crtcId = res->crtcs[i];
			printf("crtcs %lu: x: %i, y: %i, width: %i, height: %i\n",
					crtcId, ci->x,
					ci->y, ci->.width,
					ci->.height);

			XRRFreeCrtcInfo(ci);

		}
	}
#endif

	unsigned long currentEvent = 0;
	bool handledEvent;

	while (1) {
		handledEvent = false;
		sc = XRRGetScreenInfo(dpy, DefaultRootWindow(dpy));
		if (sc)
			XRRFreeScreenConfigInfo(sc);
		while (XPending(dpy)) {

			XNextEvent(dpy, &event);

			switch (event.type - randrEventBase) {
			case RRScreenChangeNotify: {
				handledEvent = true;
				printf("got XRRScreenChangeNotifyEvent\n");
				XRRScreenChangeNotifyEvent *aevent = (XRRScreenChangeNotifyEvent *) &event;

				currentEvent = aevent->serial;

				XRRScreenResources *res = XRRGetScreenResources(dpy, DefaultRootWindow(dpy));

#ifdef DEBUG
				printf("crtcs:\n");
				for (int i = 0; i < res->ncrtc; i++) {
					printf("\t%lu\n", res->crtcs[i]);
				}
				printf("\noutputs:\n");
				for (int i = 0; i < res->noutput; i++) {
					printf("\t%lu\n", res->outputs[i]);
				}

				printf("\nmodes:\n");
				for (int i = 0; i < res->nmode; i++) {
					printf("\tid: %lu, width: %i, height: %i, name: %s\n",
							res->modes[i].id, res->modes[i].width,
							res->modes[i].height, res->modes[i].name);
				}
#endif
				XRRFreeScreenResources(res);
				break;
			}
			case RRNotify: {
				handledEvent = true;
				XRRNotifyEvent *aevent = (XRRNotifyEvent *) &event;
				currentEvent = aevent->serial;

				switch (aevent->subtype) {
				case RRNotify_OutputChange: {
					printf("got XRROutputChangeNotifyEvent\n");
					XRROutputChangeNotifyEvent *aevent = (XRROutputChangeNotifyEvent *) &event;
					//XRRScreenResources *res = XRRGetScreenResources(dpy,
					//		DefaultRootWindow(dpy));
					RROutput outputId = aevent->output;
					oi = XRRGetOutputInfo(dpy, res, outputId);

					/*
					 // store new OutputInfo
					 if (outputs.count(outputId) > 0) {
					 XRRFreeOutputInfo(outputs[aevent->output]);
					 }
					 outputs[aevent->output] = oi; */

					RRCrtc crtcId = oi->crtc;

					printf("\tOutputInfo:\n");
					printf("\tid: name: %s, connected: %i, crtc: %lu\n\n", oi->name, oi->connection, crtcId);

					if (oi->connection == 1) {
						if (connected_outputs.count(outputId) > 0) { // crtc is now disconnected
							connected_outputs.erase(outputId);
						}
						disconnected_outputs[outputId] = oi;

						printf("\t-> crtc %lu is disconnected\n", crtcId);
					} else {
						if (disconnected_outputs.count(outputId) > 0) { // crtc is now disconnected
							disconnected_outputs.erase(outputId);
						}
						printf("\t-> crtc %lu is connected\n", crtcId);
					}
					/*					if (crtcId != 0) {
					 if (oi->connection == 1) { // disconnect
					 if (connected_crtcs.count(crtcId) > 0) { // crtc is now disconnected
					 if (disconnected_crtcs.count(crtcId) == 0) { // not marked as disconnected
					 disconnected_crtcs[crtcId] = connected_crtcs[crtcId];
					 }

					 connected_crtcs.erase(crtcId);

					 printf("\t-> crtc %lu is diconnected\n", crtcId);
					 }
					 }
					 */
					XRRFreeScreenResources(res);
					//available_crtcs.clear();
					//connected_crtcs.clear();

					res = XRRGetScreenResources(dpy, DefaultRootWindow(dpy));

					scan(dpy, res);
//					}
					//XRRFreeScreenResources(res);
					break;
				}
				case RRNotify_CrtcChange: {
					printf("got XRRCrtcChangeNotifyEvent\n");
					XRRCrtcChangeNotifyEvent *aevent = (XRRCrtcChangeNotifyEvent *) &event;
					//XRRScreenResources *res = XRRGetScreenResources(dpy,
					//		DefaultRootWindow(dpy));

					RRCrtc crtcId = aevent->crtc;
					ci = XRRGetCrtcInfo(dpy, res, crtcId);
					/*
					 // free OutputInfo if not in connected crtc
					 if (available_crtcs.count(crtcId) > 0 && connected_crtcs.count(crtcId) == 0) {
					 XRRFreeCrtcInfo(available_crtcs[crtcId]);
					 }
					 // store new OutputInfo
					 available_crtcs[crtcId] = ci;
					 */
					printf("\tCrtcInfo:\n");
					printf("\tcrtcs %lu: x: %i, y: %i, width: %i, height: %i\n", crtcId, ci->x, ci->y, ci->width,
							ci->height);

					if (ci->mode != 0 && ci->width != 0 && ci->height != 0) { // we have valid data
					/*
					 if (disconnected_crtcs.count(crtcId) > 0) { // marked as disconnected
					 XRRFreeCrtcInfo (disconnected_crtcs[crtcId]);
					 disconnected_crtcs.erase(crtcId);
					 }
					 if (connected_crtcs.count(crtcId) != 0) { // crtc is connected
					 XRRFreeCrtcInfo (connected_crtcs[crtcId]);
					 }
					 connected_crtcs[crtcId] = ci;
					 */
						printf("\tcrtc %lu is connected\n", crtcId);
					} else {
						/*
						 if (connected_crtcs.count(crtcId) != 0) { // marked as connected
						 XRRFreeCrtcInfo (connected_crtcs[crtcId]);
						 connected_crtcs.erase(crtcId);
						 }

						 if (disconnected_crtcs.count(crtcId) > 0) { // marked as disconnected
						 XRRFreeCrtcInfo (disconnected_crtcs[crtcId]);
						 disconnected_crtcs.erase(crtcId);
						 }
						 disconnected_crtcs[crtcId] = ci;
						 */
						crtc_disable(dpy, res, crtcId);

						printf("\tcrtc %lu is disconnected\n", crtcId);

					}
					//XRRFreeScreenResources(res);
					XRRFreeCrtcInfo(ci);
					break;
				}
				case RRNotify_OutputProperty: {
					printf("got XRROutputPropertyNotifyEvent\n");
					XRROutputPropertyNotifyEvent * aevent = (XRROutputPropertyNotifyEvent *) &event;
					currentEvent = aevent->serial;

					break;
				}
				}
				break;
			}
			}
		}

		if (handledEvent)
			handleChanges(currentEvent, false);
		sleep(2);
	}
	return EXIT_SUCCESS;
}

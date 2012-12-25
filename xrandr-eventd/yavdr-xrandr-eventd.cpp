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

static std::map<RROutput, XRROutputInfo *> outputs;
static std::map<RROutput, XRROutputInfo *> connected_outputs;
static std::map<RROutput, XRROutputInfo *> disconnected_outputs;
static std::map<RROutput, bool> lastConnectionState; // false if crtc is disconnected

//static std::map<RRCrtc, XRRCrtcInfo *> connected_crtcs;
//static std::map<RRCrtc, XRRCrtcInfo *> disconnected_crtcs;
//static std::map<RRCrtc, XRRCrtcInfo *> available_crtcs;
//static std::map<RRCrtc, bool> lastConnectionState; // false if crtc is disconnected

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
	//disconnected_outputs.clear();

	for (int i = 0; i < res->noutput; i++) {
		if ((oi = XRRGetOutputInfo(dpy, res, res->outputs[i])) != NULL) {
			RROutput outputId = res->outputs[i];
			if (outputs.count(outputId) == 0) {
				outputs[outputId] = oi;
				printf("\tid: %lu: name: %s, connection: %i, crtc: %lu crtcs:", outputId, oi->name, oi->connection,
						oi->crtc);
				for (int j = 0; j < oi->ncrtc; j++) {
					printf(" %lu", oi->crtcs[j]);
				}
				printf("\n");
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

						printf("\tavailable crtcs %lu: x: %i, y: %i, width: %i, height: %i outputs:", crtcId, ci->x,
								ci->y, ci->width, ci->height);
						for (int j = 0; j < ci->noutput; j++) {
							printf(" %lu", ci->outputs[j]);
						}
						printf("\n");

						if (ci->mode != 0 && ci->width != 0
								&& ci->height != 0 /*&& connected_crtcs.count(crtcId) == 0*/) { // we have valid data -> crtc is connected
								//connected_crtcs[crtcId] = ci;

							printf("\tcrtc %lu is connected\n", crtcId);
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

								printf("\tavailable crtcs %lu: x: %i, y: %i, width: %i, height: %i outputs:", crtcId,
										ci->x, ci->y, ci->width, ci->height);
								for (int j = 0; j < ci->noutput; j++) {
									printf(" %lu", ci->outputs[j]);
								}
								printf("\n");

								if (ci->mode != 0 && ci->width != 0 && ci->height != 0/*
								 && connected_crtcs.count(crtcId) == 0*/) { // wie have valid data -> crtc is connected

								//connected_crtcs[crtcId] = ci;

									printf("\tcrtc %lu is connected\n", crtcId);
								}
								//XRRFreeCrtcInfo(ci);
							//}
							//	}
							//}
							XRRFreeCrtcInfo(ci);
						}
					}
				}

			} else {
				if (oi->crtc != 0) { // output disconnected but crtc enables
					crtc_disable(dpy, res, oi->crtc);
				}
			}

			//XRRFreeOutputInfo(oi);
		}
	}
}
void handleChanges(unsigned long currentEvent) {
	if (currentEvent != lastHandledEvent) {
		bool callScript = false;
		printf("handleChanges:\n");
		printf("--------------\n");
		printf("\tstart - connected crtc: %lu, disconnected crtc: %lu\n", connected_outputs.size(),
				disconnected_outputs.size());

		for (std::map<RROutput, XRROutputInfo *>::iterator it = connected_outputs.begin();
				it != connected_outputs.end(); it++) {
			XRROutputInfo *oi = (*it).second;

			if (oi->connection == 0) {
				printf("%lu: %s is connected\n", (*it).first, oi->name);
			}
			/*
			 for (int i = 0; i < ci->noutput; i++) {
			 RROutput oId = ci->outputs[i];
			 if (outputs[oId]->connection == 0) {
			 printf("%lu: %s is connected\n", (*it).first, outputs[oId]->name);
			 }
			 }
			 */
			if (!lastConnectionState[(*it).first]) {
				callScript = true;
			}
			lastConnectionState[(*it).first] = true;
		}

		for (std::map<RROutput, XRROutputInfo *>::iterator it = disconnected_outputs.begin();
				it != disconnected_outputs.end(); it++) {
			XRROutputInfo *oi = (*it).second;

			if (oi->connection == 1) {
				printf("%lu: %s is disconnected\n", (*it).first, oi->name);
			}
			/*
			 for (int i = 0; i < ci->noutput; i++) {
			 RROutput oId = ci->outputs[i];
			 if (outputs[oId]->connection == 1) {
			 printf("%lu: %s is disconnected\n", (*it).first, outputs[oId]->name);
			 }
			 }
			 */
			disconnected_outputs.erase((*it).first);

			if (lastConnectionState[(*it).first]) {
				callScript = true;
			}
			lastConnectionState[(*it).first] = false;

			//XRRFreeCrtcInfo(ci);
			XRRFreeOutputInfo(oi);
		}

		lastHandledEvent = currentEvent;

		printf("\tend   - connected crtc: %lu, disconnected crtc: %lu\n", connected_outputs.size(),
				disconnected_outputs.size());

		if (callScript) {
			printf("!!! We have to update X11 !!!\n");
		}
		printf("==============\n\n");

	}
}

int main(int argc, char **argv) {
	XEvent event;
	Display *dpy;
	uid_t uid;
	XRRScreenConfiguration *sc = NULL;
	int randrEventBase;
	int error_base;

	if (((uid = getuid()) == 0) || uid != geteuid())
		xerror("%s may not run as root\n", NAME);

	if ((dpy = XOpenDisplay(NULL)) == NULL)
		xerror("Cannot open display\n");
	XRRSelectInput(dpy, DefaultRootWindow(dpy),
			RRScreenChangeNotifyMask | RRCrtcChangeNotifyMask | RROutputChangeNotifyMask | RROutputPropertyNotifyMask);
	XSync(dpy, False);
	XSetIOErrorHandler((XIOErrorHandler) error_handler);
	XRRQueryExtension(dpy, &randrEventBase, &error_base);
	XRRScreenResources *res = XRRGetScreenResources(dpy, DefaultRootWindow(dpy));
	/*
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
	 */

	// query ScreenInfo to be sure because of NVidia
	sc = XRRGetScreenInfo(dpy, DefaultRootWindow(dpy));
	if (sc)
		XRRFreeScreenConfigInfo(sc);

	XRROutputInfo *oi = NULL;
	XRRCrtcInfo *ci = NULL;

	scan(dpy, res);

	handleChanges(0);

	/*
	 for (int i = 0; i < res->ncrtc; i++) {
	 if ((ci = XRRGetCrtcInfo(dpy, res, res->crtcs[i])) != NULL) {
	 RRCrtc crtcId = res->crtcs[i];
	 crtcs[crtcId] = ci;
	 XRRFreeCrtcInfo(ci);
	 printf("crtcs %lu: x: %i, y: %i, width: %i, height: %i\n",
	 crtcId, crtcs[crtcId].x,
	 crtcs[crtcId].y, crtcs[crtcId].width,
	 crtcs[crtcId].height);
	 }
	 }
	 */
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
				//printf("crtcs:\n");
				//for (int i = 0; i < res->ncrtc; i++) {
				//	printf("\t%lu\n", res->crtcs[i]);
				//}
				//printf("\noutputs:\n");
				//for (int i = 0; i < res->noutput; i++) {
				//	printf("\t%lu\n", res->outputs[i]);
				//}
				/*
				 printf("\nmodes:\n");
				 for (int i = 0; i < res->nmode; i++) {
				 printf("\tid: %lu, width: %i, height: %i, name: %s\n",
				 res->modes[i].id, res->modes[i].width,
				 res->modes[i].height, res->modes[i].name);
				 }*/
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
			handleChanges(currentEvent);
		sleep(2);
	}
	return EXIT_SUCCESS;
}

#!/bin/sh

# prefill hdf
hdf_prefill()
{
  KEY=$1
  VALUE=$2
  CURRENT=`dbget $KEY`
  if [ "x" = "x$CURRENT" ]; then
    dbset "$KEY=$VALUE"
  fi
}


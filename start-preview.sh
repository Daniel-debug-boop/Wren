#!/bin/sh
cd "$(dirname "$0")/frontend" && npm run make-i18n && node server.js

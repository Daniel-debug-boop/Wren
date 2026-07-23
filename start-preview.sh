#!/bin/sh
cd "$(dirname "$0")/frontend" && npm run make-i18n && npx react-router-serve build/server/index.js

#!/bin/sh
cd /home/daytona/codebase/frontend && npm run make-i18n && npx react-router-serve build/server/index.js

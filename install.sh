#!/usr/bin/env bash

cd $(dirname "$0")
rm -rf classes/
mkdir -p classes/
unzip ~/Development/Other/wm/target/wm-1.0-SNAPSHOT-shaded.jar -d classes/

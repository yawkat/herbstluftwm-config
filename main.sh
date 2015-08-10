#!/bin/bash

hc() {
    herbstclient "$@"
}

kill $(cat .pid)
rm .pid

singleton() {
    "$@" &
    echo $! >> .pid
}

Mod=Mod4   # Use the super key as the main modifier
hc emit_hook reload
# remove all existing keybindings
hc keyunbind --all

hc rename default 1

for i in $(seq 0 9); do
    hc add $i
    hc keybind $Mod-$i use $i
    hc keybind $Mod-Shift-$i move $i
done

singleton java \
    -Xmx256M \
    -XX:InitialHeapSize=256M \
    -XX:MinHeapFreeRatio=10 \
    -XX:MaxHeapFreeRatio=30 \
    -Djava.library.path=classes/lib/x86_64/linux \
    -Dcom.lambdaworks.jni.loader=sys \
    -Xloggc:log/wm.gc.log \
    -XX:+PrintGCDetails \
    -XX:+PrintGCTimeStamps \
    -XX:+UseParallelGC \
    -cp classes at.yawk.wm.Main > /dev/null

# keybindings

hc keybind $Mod-Shift-r reload
hc keybind Mod1-F4 close
hc keybind $Mod-Return spawn gnome-terminal

# basic movement
# focusing clients
hc keybind $Mod-Left  focus left
hc keybind $Mod-Down  focus down
hc keybind $Mod-Up    focus up
hc keybind $Mod-Right focus right

# moving clients
hc keybind $Mod-Shift-Left  shift left
hc keybind $Mod-Shift-Down  shift down
hc keybind $Mod-Shift-Up    shift up
hc keybind $Mod-Shift-Right shift right

# splitting frames
# create an empty frame at the specified direction
hc keybind $Mod-u       split   bottom  0.5
hc keybind $Mod-o       split   right   0.5
# let the current frame explode into subframes
hc keybind $Mod-Control-space split explode

# resizing frames
hc keybind $Mod-Control-Left    resize left +0.05
hc keybind $Mod-Control-Down    resize down +0.05
hc keybind $Mod-Control-Up      resize up +0.05
hc keybind $Mod-Control-Right   resize right +0.05

# layouting
hc keybind $Mod-r remove
hc keybind $Mod-space cycle_layout 1
hc keybind $Mod-s floating toggle
hc keybind $Mod-f fullscreen toggle
hc keybind $Mod-p pseudotile toggle

# mouse
hc mouseunbind --all
hc mousebind $Mod-Button1 move
hc mousebind $Mod-Button2 zoom
hc mousebind $Mod-Button3 resize

# focus
hc keybind $Mod-BackSpace   cycle_monitor
hc keybind $Mod-Tab         cycle_all +1
hc keybind $Mod-Shift-Tab   cycle_all -1
hc keybind $Mod-c cycle
hc keybind $Mod-i jumpto urgent

# theme
hc attr theme.tiling.reset 1
hc attr theme.floating.reset 1
hc set frame_border_active_color '#eee8d4'
hc set frame_border_normal_color '#002b36'
hc set frame_bg_normal_color '#002b36'
hc set frame_bg_active_color '#073642'
hc set frame_border_width 1
hc set always_show_frame 1
hc set frame_bg_transparent 1
hc set frame_transparent_width 0
hc set frame_gap 8

hc attr theme.active.color '#eee8d4'
hc attr theme.normal.color '#002b36'
hc attr theme.urgent.color '#cb4b16'
hc attr theme.inner_width 1
hc attr theme.inner_color black
hc attr theme.border_width 0
hc attr theme.floating.border_width 4
hc attr theme.floating.outer_width 1
hc attr theme.floating.outer_color black
hc attr theme.active.inner_color '#073642'
hc attr theme.active.outer_color '#eee8d4'
hc attr theme.background_color '#839496'

hc set window_gap 0
hc set frame_padding 0
hc set smart_window_surroundings 0
hc set smart_frame_surroundings 1
hc set mouse_recenter_gap 0

# rules
hc unrule -F
hc rule focus=on # normally focus new clients
hc rule windowtype~'_NET_WM_WINDOW_TYPE_(DIALOG|UTILITY|SPLASH)' pseudotile=on
hc rule windowtype='_NET_WM_WINDOW_TYPE_DIALOG' focus=on
hc rule windowtype~'_NET_WM_WINDOW_TYPE_(NOTIFICATION|DOCK|DESKTOP)' manage=off

hc rule --class=Firefox --tag=3
hc rule --class=Quasselclient --tag=4
hc rule --class=Steam --tag=9
hc rule --class=Thunderbird --tag=0
hc rule --class=Rhythmbox --tag=0
hc rule --class=Sublime_text --tag=2

db="dbus-send --print-reply --dest=org.mpris.MediaPlayer2.spotify /org/mpris/MediaPlayer2"
hc keybind $Mod-Pause spawn $db org.mpris.MediaPlayer2.Player.PlayPause
hc keybind $Mod-Insert spawn $db org.mpris.MediaPlayer2.Player.Previous
hc keybind $Mod-Delete spawn $db org.mpris.MediaPlayer2.Player.Next

hc keybind XF86AudioPlay spawn $db org.mpris.MediaPlayer2.Player.PlayPause
hc keybind XF86AudioStop spawn $db org.mpris.MediaPlayer2.Player.Stop
hc keybind XF86AudioPrev spawn $db org.mpris.MediaPlayer2.Player.Previous
hc keybind XF86AudioNext spawn $db org.mpris.MediaPlayer2.Player.Next

hc keybind XF86Launch8 spawn setxkbmap de nodeadkeys
hc keybind XF86Launch9 spawn setxkbmap us

hc keybind $Mod-period spawn xbacklight +10
hc keybind $Mod-comma spawn xbacklight -10
hc keybind XF86MonBrightnessUp spawn xbacklight +10
hc keybind XF86MonBrightnessDown spawn xbacklight -10

hc set default_frame_layout 2

# unlock, just to be sure
hc unlock

herbstclient set tree_style '╾│ ├└╼─┐'

singleton xfce4-volumed-pulse --no-daemon

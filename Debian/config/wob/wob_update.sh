# Display current volume by piping pactl output to wob.sock

isMuted=$(pactl get-sink-mute @DEFAULT_SINK@ | grep -Po "no|yes")

if [ "$isMuted" = "no" ]; then
  pactl get-sink-volume @DEFAULT_SINK@ | grep -Po "[\d]{1,3}(?=%)" | head -1 >$XDG_RUNTIME_DIR/wob.sock
else
  echo 0 >$XDG_RUNTIME_DIR/wob.sock
fi

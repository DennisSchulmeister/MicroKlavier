import _thread, time
from turtle import back
from webbrowser import BackgroundBrowser

# Background thread: Print message each 1000ms
def background_thread():
    # Wait 500ms
    prev_time = time.ticks_ms()
    while time.ticks_diff(time.ticks_ms(), prev_time) < 500:
        pass

    # Print message each 1000ms
    prev_time = time.ticks_ms()

    while True:
        if time.ticks_diff(time.ticks_ms(), prev_time) >= 1000:
            prev_time = time.ticks_ms()
            print("Main Loop")

_thread.start_new_thread(background_thread)


# Main Loop: Print message each 1000ms
prev_time = time.ticks_ms()

while True:
    if time.ticks_diff(time.ticks_ms(), prev_time) >= 1000:
        prev_time = time.ticks_ms()
        print("Main Loop")
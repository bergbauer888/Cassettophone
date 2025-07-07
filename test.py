import subprocess

# List of overlay instructions
overlays = [
    {
        "image_path": "culala/resized_donald_trump.png",
        "start_time": 1,
        "end_time": 10,
        "position": "bottom-left",
    },
    {
        "image_path": "culala/resized_joe_biden.png",
        "start_time": 12,
        "end_time": 14,
        "position": "bottom-left",
    },
    {
        "image_path": "culala/resized_summary.png",
        "start_time": 1,
        "end_time": 10,
        "position": "top-middle",
    },
    {
        "image_path": "culala/resized_joe_biden.png",
        "start_time": 15,
        "end_time": 21,
        "position": "bottom-left",
    },
]
video_file = "culala/backdrop.mp4"


def get_position(position):
    if position == "bottom-left":
        return "W-w-10:H-h-10"  # Position at bottom left (10px from both sides)
    elif position == "top-middle":
        return "(W-w)/2:10"  # Position at top middle (10px from the top)
    else:
        return "0:0"  # Default position (top-left)


# Prepare the filter complex parts
filter_complex_parts = []
# Generate the filter_complex for each overlay
for idx, overlay in enumerate(overlays):
    image_path = overlay["image_path"]
    start_time = overlay["start_time"]
    end_time = overlay["end_time"]
    position = get_position(overlay["position"])
    # Create a unique output label for each overlay (e.g., v1-10, v12-14)
    output_label = f"[v{start_time}-{end_time}]"
    # Append the overlay command to the filter_complex list
    if idx == 0:
        filter_complex_parts.append(
            f"[0:v][{idx+1}:v]overlay={position}:enable='between(t,{start_time},{end_time})'{output_label}"
        )
    else:
        # For subsequent overlays, chain them to the previous output
        filter_complex_parts.append(
            f"[v{overlays[idx-1]['start_time']}-{overlays[idx-1]['end_time']}]"
            f"[{idx+1}:v]overlay={position}:enable='between(t,{start_time},{end_time})'{output_label}"
        )
# Join all overlay filter parts into a single string
filter_complex = ",".join(filter_complex_parts)
# FFmpeg command
command = ["ffmpeg", "-i", video_file]
# Add input images to the command
for overlay in overlays:
    command += ["-i", overlay["image_path"]]
# Add the filter_complex to the command
command += ["-filter_complex", filter_complex]
# Map the final video output to [v], and copy the audio stream
command += [
    "-map",
    f'[v{overlays[-1]["start_time"]}-{overlays[-1]["end_time"]}]',
    "-c:a",
    "copy",
    "output_video.mp4",
]
# Execute the command
subprocess.run(command)

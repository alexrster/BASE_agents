#!/usr/bin/env python3
"""
Generate an image showing electricity grid availability for a given date.
Image size: 1024x250px
Follows iOS design guidelines with SF Pro font and system colors.
"""

import json
import sys
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

# iOS System Colors (Light Mode)
COLOR_AVAILABLE = (52, 199, 89)  # iOS System Green
COLOR_UNAVAILABLE = (255, 107, 0)  # Hot Orange for unavailable
COLOR_BACKGROUND = (255, 255, 255)  # iOS System Background (Light Gray)
COLOR_CARD_BACKGROUND = (255, 255, 255)  # White for card
COLOR_PRIMARY_TEXT = (0, 0, 0)  # iOS Label (Primary)
COLOR_SECONDARY_TEXT = (60, 60, 67)  # iOS Secondary Label
COLOR_SEPARATOR = (198, 198, 200)  # iOS Separator
COLOR_TIMELINE = (142, 142, 147)  # Gray timeline color
COLOR_TIMELINE_TICK = (174, 174, 178)  # Lighter gray for tick marks
COLOR_CURRENT_TIME = (128, 128, 128)  # iOS System Blue for current time marker

# Image dimensions (default horizontal)
WIDTH = 1024
HEIGHT = 250
MARGIN = 24  # iOS standard margin
CARD_PADDING = 16  # iOS card padding
CORNER_RADIUS = 12  # iOS standard corner radius


def get_hour_state(data, hour):
    """Get the state for a specific hour (0-23)."""
    key = f"T_{hour:02d}"
    return data.get(key, "●")


def draw_rounded_rectangle(draw, bbox, radius, fill=None, outline=None, width=1):
    """Draw a rounded rectangle with iOS-style rounded corners."""
    x1, y1, x2, y2 = bbox
    radius = min(radius, (x2 - x1) / 2, (y2 - y1) / 2)  # Ensure radius fits
    
    if fill:
        # Draw main rectangle body
        draw.rectangle([x1 + radius, y1, x2 - radius, y2], fill=fill)
        draw.rectangle([x1, y1 + radius, x2, y2 - radius], fill=fill)
        
        # Draw rounded corner circles
        draw.ellipse([x1, y1, x1 + 2*radius, y1 + 2*radius], fill=fill)
        draw.ellipse([x2 - 2*radius, y1, x2, y1 + 2*radius], fill=fill)
        draw.ellipse([x1, y2 - 2*radius, x1 + 2*radius, y2], fill=fill)
        draw.ellipse([x2 - 2*radius, y2 - 2*radius, x2, y2], fill=fill)
    
    if outline:
        # Draw outline using lines and arcs
        # Top edge
        draw.line([(x1 + radius, y1), (x2 - radius, y1)], fill=outline, width=width)
        # Bottom edge
        draw.line([(x1 + radius, y2), (x2 - radius, y2)], fill=outline, width=width)
        # Left edge
        draw.line([(x1, y1 + radius), (x1, y2 - radius)], fill=outline, width=width)
        # Right edge
        draw.line([(x2, y1 + radius), (x2, y2 - radius)], fill=outline, width=width)
        # Rounded corners (arcs)
        draw.arc([x1, y1, x1 + 2*radius, y1 + 2*radius], 180, 270, fill=outline, width=width)
        draw.arc([x2 - 2*radius, y1, x2, y1 + 2*radius], 270, 360, fill=outline, width=width)
        draw.arc([x1, y2 - 2*radius, x1 + 2*radius, y2], 90, 180, fill=outline, width=width)
        draw.arc([x2 - 2*radius, y2 - 2*radius, x2, y2], 0, 90, fill=outline, width=width)


def get_ios_font(size, weight="regular"):
    """Get iOS SF Pro font or fallback to system font."""
    font_paths = [
        f"/System/Library/Fonts/Supplemental/SF-Pro-Text-{weight.capitalize()}.otf",
        f"/System/Library/Fonts/Supplemental/SFProText-{weight.capitalize()}.otf",
        "/System/Library/Fonts/Supplemental/SF-Pro-Text-Regular.otf",
        "/System/Library/Fonts/Supplemental/SFProText-Regular.otf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/Library/Fonts/Arial.ttf",
    ]
    
    for path in font_paths:
        try:
            return ImageFont.truetype(path, size)
        except:
            continue
    
    return ImageFont.load_default()


def draw_dashed_line(draw, points, fill, width=1, dash_length=5, gap_length=3):
    """Draw a dashed line between two points.
    
    Args:
        draw: ImageDraw object
        points: List of two tuples [(x1, y1), (x2, y2)]
        fill: Color tuple
        width: Line width
        dash_length: Length of each dash segment
        gap_length: Length of gap between dashes
    """
    if len(points) != 2:
        return
    
    x1, y1 = points[0]
    x2, y2 = points[1]
    
    # Calculate total line length
    dx = x2 - x1
    dy = y2 - y1
    total_length = (dx**2 + dy**2)**0.5
    
    if total_length == 0:
        return
    
    # Normalize direction vector
    unit_x = dx / total_length
    unit_y = dy / total_length
    
    # Draw dashes
    current_pos = 0
    while current_pos < total_length:
        # Start of dash
        dash_start_x = x1 + unit_x * current_pos
        dash_start_y = y1 + unit_y * current_pos
        
        # End of dash (either dash_length or remaining distance)
        dash_end_pos = min(current_pos + dash_length, total_length)
        dash_end_x = x1 + unit_x * dash_end_pos
        dash_end_y = y1 + unit_y * dash_end_pos
        
        # Draw the dash segment
        draw.line([(dash_start_x, dash_start_y), (dash_end_x, dash_end_y)],
                 fill=fill, width=width)
        
        # Move to next dash position
        current_pos += dash_length + gap_length


def get_previous_state(data, hour):
    """Get the state of the previous hour, or current if hour is 0."""
    if hour == 0:
        return get_hour_state(data, 0)
    return get_hour_state(data, hour - 1)


def get_next_state(data, hour):
    """Get the state of the next hour, or current if hour is 23."""
    if hour == 23:
        return get_hour_state(data, 23)
    return get_hour_state(data, hour + 1)


def get_state_color(state):
    """Get the color for a given state."""
    if state == "●":
        return COLOR_AVAILABLE
    elif state == "✕":
        return COLOR_UNAVAILABLE
    else:
        return COLOR_TIMELINE  # Default gray


def is_today(tdate_str):
    """Check if TDate matches today's date. TDate format: DD-MM-YYYY"""
    try:
        # Parse TDate (format: DD-MM-YYYY)
        tdate = datetime.strptime(tdate_str, "%d-%m-%Y")
        today = datetime.now().date()
        return tdate.date() == today
    except:
        return False


def get_current_time_position():
    """Get the current hour and minute as a position (0.0 to 24.0)."""
    now = datetime.now()
    return now.hour + now.minute / 60.0


def draw_timeline(draw, data, tdate, timeline_y, width, height, vertical=False, timeline_card_height=None):
    """Draw a continuous line graph showing electricity availability."""
    if vertical:
        # Vertical orientation: timeline goes from top to bottom
        # Use timeline_card_height if provided, otherwise calculate from height
        if timeline_card_height is not None:
            timeline_height = timeline_card_height - 40  # Account for padding inside card
        else:
            timeline_height = height - 2 * MARGIN - 2 * CARD_PADDING - 120  # Reserve space for date/legend
        timeline_x = MARGIN + CARD_PADDING + 70  # Leave space for hour labels on left (increased for "05:00")
        timeline_y_start = timeline_y + 20  # Reduced spacing since no title
        hour_height = timeline_height / 24
        line_x = timeline_x + 20  # X position for the availability line
        line_width = 6  # Thickness of the line
        timeline_axis_x = line_x  # Position of the gray timeline axis
        
        # Draw gray timeline axis (vertical line)
        draw.line([(timeline_axis_x, timeline_y_start), 
                   (timeline_axis_x, timeline_y_start + timeline_height)],
                  fill=COLOR_TIMELINE, width=2)
        
        # Draw hour markers (tick marks and labels)
        font_small = get_ios_font(10, "regular")
        tick_length = 8
        
        for hour in range(24):
            y_pos = timeline_y_start + hour * hour_height
            
            # Draw tick mark
            draw.line([(timeline_axis_x - tick_length / 2, y_pos),
                       (timeline_axis_x + tick_length / 2, y_pos)],
                      fill=COLOR_TIMELINE_TICK, width=1)
            
            # Draw hour label (to the left of the timeline)
            hour_label = f"{hour:02d}:00"
            text_bbox = draw.textbbox((0, 0), hour_label, font=font_small)
            text_height = text_bbox[3] - text_bbox[1]
            text_y = y_pos - text_height / 2
            draw.text((timeline_axis_x - tick_length / 2 - 35, text_y), hour_label,
                     fill=COLOR_SECONDARY_TEXT, font=font_small)
        
        # Build line segments
        line_segments = []
        
        for hour in range(24):
            state = get_hour_state(data, hour)
            hour_start_y = timeline_y_start + hour * hour_height
            hour_end_y = timeline_y_start + (hour + 1) * hour_height
            hour_mid_y = timeline_y_start + hour * hour_height + hour_height / 2
            
            if state == "%":
                # Partial: previous state to middle, next state from middle
                prev_state = get_previous_state(data, hour)
                next_state = get_next_state(data, hour)
                
                # First half: previous state
                prev_color = get_state_color(prev_state)
                line_segments.append({
                    'start_y': hour_start_y,
                    'end_y': hour_mid_y,
                    'color': prev_color
                })
                
                # Second half: next state
                next_color = get_state_color(next_state)
                line_segments.append({
                    'start_y': hour_mid_y,
                    'end_y': hour_end_y,
                    'color': next_color
                })
            else:
                # Full hour: single state
                color = get_state_color(state)
                line_segments.append({
                    'start_y': hour_start_y,
                    'end_y': hour_end_y,
                    'color': color
                })
        
        # Draw continuous line segments (vertical)
        for segment in line_segments:
            # Draw thick line segment (vertical)
            draw.line([(line_x, segment['start_y']),
                       (line_x, segment['end_y'])],
                      fill=segment['color'], width=line_width)
        
        # Draw horizontal separators at hour boundaries (subtle)
        for hour in range(1, 24):
            y_pos = timeline_y_start + hour * hour_height
            draw.line([(line_x - line_width / 2 - 2, y_pos),
                       (line_x + line_width / 2 + 2, y_pos)],
                      fill=COLOR_TIMELINE_TICK, width=1)
        
        # Draw current time marker if TDate is today
        tdate = data.get("T_Date", "")
        if is_today(tdate):
            current_time_pos = get_current_time_position()
            if 0 <= current_time_pos < 24:
                current_y = timeline_y_start + (current_time_pos / 24.0) * timeline_height
                
                # Draw horizontal line marker
                marker_left = line_x - line_width / 2 - 3
                marker_right = line_x + line_width / 2 + 9
                            
                # Draw triangle pointer to the right of the line
                triangle_size = 3
                triangle_points = [
                    (marker_right, current_y - triangle_size),
                    (marker_right, current_y + triangle_size),
                    (marker_right - 2*triangle_size, current_y)
                ]
                draw.polygon(triangle_points, fill=COLOR_CURRENT_TIME)

                # Draw "now" label (to the right of the triangle)
                text_bbox = draw.textbbox((0, 0), "now", font=font_small)
                text_width = text_bbox[2] - text_bbox[0]
                draw.text((marker_right + triangle_size + 4, current_y - triangle_size - 12), "now", 
                         fill=COLOR_CURRENT_TIME, font=font_small)
                
                # Draw dashed horizontal line (to the right)
                draw_dashed_line(draw, 
                               [(marker_right - 10, current_y), (marker_right + 30, current_y)], 
                               fill=COLOR_CURRENT_TIME, 
                               width=1,
                               dash_length=4,
                               gap_length=6)
    else:
        # Horizontal orientation (original)
        # Calculate dimensions
        timeline_width = width - 2 * MARGIN - 2 * CARD_PADDING
        timeline_x = MARGIN + CARD_PADDING
        hour_width = timeline_width / 24
        line_y = timeline_y + 40  # Y position for the availability line
        line_height = 6  # Thickness of the line
        timeline_axis_y = line_y  # Position of the gray timeline axis
        
        # Draw gray timeline axis (horizontal line)
        draw.line([(timeline_x, timeline_axis_y), 
                   (timeline_x + timeline_width, timeline_axis_y)],
                  fill=COLOR_TIMELINE, width=2)
        
        # Draw hour markers (tick marks and labels)
        font_small = get_ios_font(10, "regular")
        tick_length = 8
        
        for hour in range(24):
            x_pos = timeline_x + hour * hour_width
            
            # Draw tick mark
            draw.line([(x_pos, timeline_axis_y - tick_length / 2),
                       (x_pos, timeline_axis_y + tick_length / 2)],
                      fill=COLOR_TIMELINE_TICK, width=1)
            
            # Draw hour label
            hour_label = f"{hour:02d}:00"
            text_bbox = draw.textbbox((0, 0), hour_label, font=font_small)
            text_width = text_bbox[2] - text_bbox[0]
            text_x = x_pos - text_width / 2
            draw.text((text_x, timeline_axis_y + tick_length / 2 + 4), hour_label,
                     fill=COLOR_SECONDARY_TEXT, font=font_small)
        
        # Build line segments
        line_segments = []
        
        for hour in range(24):
            state = get_hour_state(data, hour)
            hour_start_x = timeline_x + hour * hour_width
            hour_end_x = timeline_x + (hour + 1) * hour_width
            hour_mid_x = timeline_x + hour * hour_width + hour_width / 2
            
            if state == "%":
                # Partial: previous state to middle, next state from middle
                prev_state = get_previous_state(data, hour)
                next_state = get_next_state(data, hour)
                
                # First half: previous state
                prev_color = get_state_color(prev_state)
                line_segments.append({
                    'start_x': hour_start_x,
                    'end_x': hour_mid_x,
                    'color': prev_color
                })
                
                # Second half: next state
                next_color = get_state_color(next_state)
                line_segments.append({
                    'start_x': hour_mid_x,
                    'end_x': hour_end_x,
                    'color': next_color
                })
            else:
                # Full hour: single state
                color = get_state_color(state)
                line_segments.append({
                    'start_x': hour_start_x,
                    'end_x': hour_end_x,
                    'color': color
                })
        
        # Draw continuous line segments
        for segment in line_segments:
            # Draw thick line segment
            draw.line([(segment['start_x'], line_y),
                       (segment['end_x'], line_y)],
                      fill=segment['color'], width=line_height)
        
        # Draw vertical separators at hour boundaries (subtle)
        for hour in range(1, 24):
            x_pos = timeline_x + hour * hour_width
            draw.line([(x_pos, line_y - line_height / 2 - 2),
                       (x_pos, line_y + line_height / 2 + 2)],
                      fill=COLOR_TIMELINE_TICK, width=1)
        
        # Draw current time marker if TDate is today
        tdate = data.get("T_Date", "")
        if is_today(tdate):
            current_time_pos = get_current_time_position()
            if 0 <= current_time_pos < 24:
                current_x = timeline_x + (current_time_pos / 24.0) * timeline_width
                
                # Draw vertical line marker
                marker_top = line_y - line_height / 2 - 9
                marker_bottom = line_y + line_height / 2 - 3
                            
                # Draw triangle pointer above the line
                triangle_size = 3
                triangle_points = [
                    (current_x - triangle_size, marker_top),
                    (current_x + triangle_size, marker_top),
                    (current_x, marker_top + 2*triangle_size)
                ]
                draw.polygon(triangle_points, fill=COLOR_CURRENT_TIME)

                # Draw "now" label
                draw.text((current_x + triangle_size, marker_top - triangle_size - 10), "now", 
                         fill=COLOR_CURRENT_TIME, font=font_small)
                
                # Draw dashed vertical line
                draw_dashed_line(draw, 
                               [(current_x, marker_top - 30), (current_x, marker_top + 40)], 
                               fill=COLOR_CURRENT_TIME, 
                               width=1,
                               dash_length=4,
                               gap_length=6)


def generate_image(data, output_path="grid_availability.png", vertical=False):
    """Generate the electricity grid availability image.
    
    Args:
        data: Dictionary containing grid availability data
        output_path: Path to save the image
        vertical: If True, generate vertical image (250x1024px), else horizontal (1024x250px)
    """
    # Set dimensions based on orientation
    if vertical:
        img_width = 250
        img_height = 1024
    else:
        img_width = WIDTH
        img_height = HEIGHT
    
    # Create image with iOS background color
    img = Image.new('RGB', (img_width, img_height), COLOR_BACKGROUND)
    draw = ImageDraw.Draw(img)
    
    # Get date from data
    tdate = data.get("T_Date", "Unknown Date")
    
    # Draw main card with rounded corners
    card_x = MARGIN
    card_y = MARGIN
    card_width = img_width - 2 * MARGIN
    card_height = img_height - 2 * MARGIN
    
    # Draw card background with rounded corners
    draw_rounded_rectangle(
        draw,
        [card_x, card_y, card_x + card_width, card_y + card_height],
        CORNER_RADIUS,
        fill=COLOR_CARD_BACKGROUND
    )
    
    if vertical:
        # Vertical layout
        # Draw date only (no title)
        font_date = get_ios_font(14, "semibold")
        
        date_text = tdate
        
        date_bbox = draw.textbbox((0, 0), date_text, font=font_date)
        date_height = date_bbox[3] - date_bbox[1]
        date_width = date_bbox[2] - date_bbox[0]
        date_x = (img_width - date_width) / 2
        date_y = MARGIN + 16
        
        draw.text((date_x, date_y), date_text, 
                 fill=COLOR_PRIMARY_TEXT, font=font_date)
        
        # Draw separator line (horizontal)
        separator_y = date_y + date_height + 12
        draw.line([(MARGIN + CARD_PADDING, separator_y), 
                   (img_width - MARGIN - CARD_PADDING, separator_y)],
                  fill=COLOR_SEPARATOR, width=1)
        
        # Draw timeline card (vertical)
        timeline_card_y = separator_y + 8
        # Calculate legend height: 2 items * 20px spacing + padding
        legend_height = 2 * 20 + 16
        timeline_card_height = img_height - timeline_card_y - MARGIN - legend_height
        timeline_card_x = MARGIN + CARD_PADDING
        timeline_card_width = img_width - 2 * MARGIN - 2 * CARD_PADDING
        
        draw_rounded_rectangle(
            draw,
            [timeline_card_x, timeline_card_y, 
             timeline_card_x + timeline_card_width, 
             timeline_card_y + timeline_card_height],
            8,
            fill=COLOR_BACKGROUND
        )
        
        # Draw timeline (vertical)
        timeline_content_y = timeline_card_y + 8
        draw_timeline(draw, data, tdate, timeline_content_y, img_width, img_height, vertical=True, timeline_card_height=timeline_card_height)
        
        # Draw legend with iOS style (vertical layout - stacked)
        legend_y = timeline_card_y + timeline_card_height + 8
        legend_x = MARGIN + CARD_PADDING
        
        legend_items = [
            ("Available", COLOR_AVAILABLE),
            ("Not Available", COLOR_UNAVAILABLE),
        ]
        
        font_legend = get_ios_font(11, "regular")
        line_indicator_width = 30
        line_indicator_height = 3
        
        for i, (label, color) in enumerate(legend_items):
            # Draw colored line indicator (horizontal)
            indicator_x = legend_x
            indicator_y = legend_y + i * 20
            draw.line([(indicator_x, indicator_y),
                       (indicator_x + line_indicator_width, indicator_y)],
                      fill=color, width=line_indicator_height)
            
            # Draw label
            draw.text((indicator_x + line_indicator_width + 8, indicator_y - 6), label, 
                     fill=COLOR_PRIMARY_TEXT, font=font_legend)
    else:
        # Horizontal layout (original)
        # Draw date only (no title)
        font_date = get_ios_font(18, "semibold")
        
        date_text = tdate
        
        date_bbox = draw.textbbox((0, 0), date_text, font=font_date)
        date_width = date_bbox[2] - date_bbox[0]
        date_x = (img_width - date_width) / 2
        
        draw.text((date_x, MARGIN + 16), date_text, fill=COLOR_PRIMARY_TEXT, font=font_date)
        
        # Draw separator line
        separator_y = MARGIN + 42
        draw.line([(MARGIN + CARD_PADDING, separator_y), 
                   (img_width - MARGIN - CARD_PADDING, separator_y)],
                  fill=COLOR_SEPARATOR, width=1)
        
        # Draw timeline card
        timeline_card_y = separator_y + 8
        timeline_card_height = 80
        timeline_card_x = MARGIN + CARD_PADDING
        timeline_card_width = img_width - 2 * MARGIN - 2 * CARD_PADDING
        
        draw_rounded_rectangle(
            draw,
            [timeline_card_x, timeline_card_y, 
             timeline_card_x + timeline_card_width, 
             timeline_card_y + timeline_card_height],
            8,
            fill=COLOR_BACKGROUND
        )
        
        # Draw timeline
        timeline_content_y = timeline_card_y + 8
        draw_timeline(draw, data, tdate, timeline_content_y, img_width, img_height, vertical=False)
        
        # Draw legend with iOS style (no symbols, just colored lines)
        legend_y = timeline_card_y + timeline_card_height + 12
        legend_x = MARGIN + CARD_PADDING
        
        legend_items = [
            ("Available", COLOR_AVAILABLE),
            ("Not Available", COLOR_UNAVAILABLE),
        ]
        
        font_legend = get_ios_font(13, "regular")
        line_indicator_width = 40
        line_indicator_height = 4
        
        for label, color in legend_items:
            # Draw colored line indicator
            indicator_y = legend_y + 8
            draw.line([(legend_x, indicator_y),
                       (legend_x + line_indicator_width, indicator_y)],
                      fill=color, width=line_indicator_height)
            
            # Draw label
            draw.text((legend_x + line_indicator_width + 10, legend_y + 2), label, 
                     fill=COLOR_PRIMARY_TEXT, font=font_legend)
            
            # Calculate next position
            label_bbox = draw.textbbox((0, 0), label, font=font_legend)
            label_width = label_bbox[2] - label_bbox[0]
            legend_x += line_indicator_width + 10 + label_width + 20
    
    # Save image
    img.save(output_path)
    print(f"Image saved to: {output_path}")


def main():
    """Main function to process input and generate image."""
    # Example data (can be overridden by command line argument)
    example_data = {
        "T_00": "●", "T_01": "●", "T_02": "●", "T_03": "●", "T_04": "●", "T_05": "●",
        "T_06": "✕", "T_07": "✕", "T_08": "✕", "T_09": "✕", "T_10": "✕", "T_11": "✕",
        "T_12": "✕", "T_13": "●", "T_14": "●", "T_15": "●", "T_16": "%", "T_17": "✕",
        "T_18": "✕", "T_19": "✕", "T_20": "✕", "T_21": "✕", "T_22": "✕", "T_23": "%",
        "T_24": "-", "T_Date": "20-11-2025"
    }
    
    # Check for vertical flag
    vertical = "--vertical" in sys.argv or "-v" in sys.argv
    if vertical:
        sys.argv = [arg for arg in sys.argv if arg not in ["--vertical", "-v"]]
    
    if len(sys.argv) > 1:
        # Read JSON from file or stdin
        input_source = sys.argv[1]
        if input_source == "-":
            # Read from stdin
            data = json.load(sys.stdin)
        else:
            # Read from file
            with open(input_source, 'r') as f:
                data = json.load(f)
    else:
        # Use example data
        data = example_data
        print("Using example data. Provide JSON file as argument or pipe JSON via stdin.")
    
    # Determine output path
    output_path = sys.argv[2] if len(sys.argv) > 2 else "grid_availability.png"
    
    # Generate image
    generate_image(data, output_path, vertical=vertical)


if __name__ == "__main__":
    main()


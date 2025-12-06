#!/usr/bin/env python3
"""
Simple script to create placeholder icons for the PhishGuard extension
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_icon(size, filename):
    # Create image with gradient-like background
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw gradient background circle
    center = size // 2
    radius = size // 2 - 4
    
    # Create a simple gradient effect
    for i in range(radius):
        alpha = int(255 * (1 - i / radius))
        color = (102, 126, 234, alpha)  # Blue gradient
        draw.ellipse([center - radius + i, center - radius + i, 
                     center + radius - i, center + radius - i], 
                    fill=color)
    
    # Draw shield emoji or text
    try:
        # Try to use a font for the shield
        font_size = size // 3
        font = ImageFont.truetype("arial.ttf", font_size)
        text = "🛡"
    except:
        # Fallback to default font
        font_size = size // 4
        font = ImageFont.load_default()
        text = "PG"
    
    # Get text size and center it
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    text_x = (size - text_width) // 2
    text_y = (size - text_height) // 2
    
    # Draw white text
    draw.text((text_x, text_y), text, fill=(255, 255, 255, 255), font=font)
    
    # Save the image
    img.save(filename, 'PNG')
    print(f"Created {filename} ({size}x{size})")

def main():
    # Create icons directory if it doesn't exist
    icons_dir = "extension/icons"
    os.makedirs(icons_dir, exist_ok=True)
    
    # Create different sized icons
    sizes = [16, 32, 48, 128]
    
    for size in sizes:
        filename = f"{icons_dir}/icon{size}.png"
        create_icon(size, filename)
    
    print("All icons created successfully!")

if __name__ == "__main__":
    main()

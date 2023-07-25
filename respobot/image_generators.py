import os
import math
import random
import environment_variables as env
import constants
import logging
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, date
from discord.errors import NotFound


async def generate_compass_image(guild, compass_data, time_span_text):
    image_width = 600
    image_height = 600
    avatar_size = 25
    font_size = image_width * 18 / 600
    bg = Image.new('RGBA', (image_width, image_height), color=(0, 0, 0, 255))
    font = ImageFont.truetype(env. BOT_DIRECTORY + "media/lucon.ttf", int(font_size))
    fontBig = ImageFont.truetype(env.BOT_DIRECTORY + "media/lucon.ttf", int(font_size * 2))

    margin_v_top = 0.0 * image_width
    margin_v_bottom = 0.05 * image_width
    margin_h_right = 0.05 * image_width
    margin_h_left = 0.05 * image_width

    margin_title = fontBig.size * 3
    margin_axis_label = font.size * 3

    graph_height = image_height - margin_v_top - margin_v_bottom - margin_title - margin_axis_label
    graph_width = image_width - margin_h_left - margin_h_right - margin_axis_label

    tick_length = int(font_size / 2)

    max_pts = 0
    min_pts = 1000000
    max_laps_per_inc = 0
    min_laps_per_inc = 1000000

    for member in compass_data:
        if compass_data[member]['point'][0] > max_laps_per_inc:
            max_laps_per_inc = compass_data[member]['point'][0]
        if compass_data[member]['point'][0] < min_laps_per_inc:
            min_laps_per_inc = compass_data[member]['point'][0]
        if compass_data[member]['point'][1] > max_pts:
            max_pts = compass_data[member]['point'][1]
        if compass_data[member]['point'][1] < min_pts:
            min_pts = compass_data[member]['point'][1]

    im = Image.new('RGBA', (image_width, image_height), color=(0, 0, 0, 0))
    draw = ImageDraw.Draw(im)

    pts_scale_max = int((int(max_pts / 10) + 1) * 10)
    pts_scale_min = int((int(min_pts / 10) - 1) * 10)
    if pts_scale_min < 0:
        pts_scale_min = 0

    laps_per_inc_scale_max = int(max_laps_per_inc) + 1
    laps_per_inc_scale_min = int(min_laps_per_inc) - 1
    if laps_per_inc_scale_min < 0:
        laps_per_inc_scale_min = 0

    pixels_per_tick = graph_width / (laps_per_inc_scale_max - laps_per_inc_scale_min)

    for tick_number in range(laps_per_inc_scale_min, laps_per_inc_scale_max + 1):
        x = margin_h_left + margin_axis_label + pixels_per_tick * (tick_number - laps_per_inc_scale_min)
        y = image_height - margin_v_bottom - margin_axis_label
        draw.line([(x, y + tick_length), (x, y)], fill=(255, 255, 255, 255), width=1, joint=None)
        draw.text((x, y + 2 * tick_length), str(tick_number), font=font, fill=(255, 255, 255, 255), anchor="mt")

    pixels_per_tick = graph_height / (pts_scale_max - pts_scale_min) * 10

    for tick_number in range(int(pts_scale_min / 10), int(pts_scale_max / 10 + 1)):
        x = margin_h_left + margin_axis_label
        y = image_height - margin_v_bottom - margin_axis_label - (tick_number - int(pts_scale_min / 10)) * pixels_per_tick
        draw.line([(x, y), (x - tick_length, y)], fill=(255, 255, 255, 255), width=1, joint=None)
        draw.text((x - tick_length * 2, y), str(tick_number * 10), font=font, fill=(255, 255, 255, 255), anchor="rm")

    bg = Image.alpha_composite(bg, im)

    laps_per_inc_scale = graph_width / (laps_per_inc_scale_max - laps_per_inc_scale_min)
    avg_champ_points_scale = graph_height / (pts_scale_max - pts_scale_min)

    for member in compass_data:
        compass_data[member]['point'] = (int((compass_data[member]['point'][0] - laps_per_inc_scale_min) * laps_per_inc_scale + margin_h_left + margin_axis_label - avatar_size / 2), int(image_height - margin_v_bottom - margin_axis_label - avatar_size / 2 - (compass_data[member]['point'][1] - pts_scale_min) * avg_champ_points_scale))
        filepath = await generate_avatar_image(guild, compass_data[member]['discordID'], avatar_size)
        avatar = Image.open(filepath)
        im = Image.new('RGBA', (image_width, image_height), color=(0, 0, 0, 0))
        im.paste(avatar, compass_data[member]['point'])
        bg = Image.alpha_composite(bg, im)
        avatar.close()

        if os.path.exists(filepath):
            os.remove(filepath)

    im = Image.new('RGBA', (image_width, image_height), color=(0, 0, 0, 0))
    draw = ImageDraw.Draw(im)

    # Draw the title
    draw.text((image_width * 0.5, margin_v_top + margin_title * 0.333), "r/RespoCompassMemes", font=fontBig, fill=(255, 255, 255, 255), anchor="mm")
    draw.text((image_width * 0.5, margin_v_top + margin_title * 0.666), time_span_text, font=font, fill=(255, 255, 255, 255), anchor="mm")

    # Draw chart axes
    draw.line([(margin_h_left + margin_axis_label, image_height - margin_v_bottom - margin_axis_label), (image_width - margin_h_right, image_height - margin_v_bottom - margin_axis_label)], fill=(255, 255, 255, 255), width=2, joint=None)
    draw.line([(margin_h_left + margin_axis_label, image_height - margin_v_bottom - margin_axis_label), (margin_h_left + margin_axis_label, margin_v_top + margin_title)], fill=(255, 255, 255, 255), width=2, joint=None)

    draw.text((margin_h_left + margin_axis_label + graph_width / 2, image_height - margin_axis_label / 2), "Laps Per Incident", font=font, fill=(255, 255, 255, 255), anchor="mm")

    # Text to be rotated...
    rotate_text = u'Average Championship Points'

    # Image for text to be rotated
    (left, top, right, bottom) = font.getbbox(rotate_text)
    img_txt = Image.new('L', (right - left, bottom - top))
    draw_txt = ImageDraw.Draw(img_txt)
    draw_txt.text((0, 0), rotate_text, font=font, fill=255)
    t = img_txt.rotate(90, expand=1)
    im.paste(t, (int(margin_axis_label / 2 - t.width / 2), int(image_height - margin_v_bottom - margin_axis_label - graph_height / 2 - t.height / 2)))

    bg = Image.alpha_composite(bg, im)

    return bg


async def generate_avatar_image(guild, discord_id, size):

    filepath = env.BOT_DIRECTORY + "media/tmp_avatar_" + str(datetime.now().strftime("%Y%m%d%H%M%S%f")) + ".png"
    try:
        member_obj = await guild.fetch_member(discord_id)
        if member_obj and member_obj.display_avatar is not None:
            await member_obj.display_avatar.save(filepath)
            avatar = Image.open(filepath)
            base = Image.new("RGBA", avatar.size, (0, 0, 0, 0))
            mask = Image.new("L", avatar.size, 0)
            draw_mask = ImageDraw.Draw(mask)
            min_dim = avatar.width
            if avatar.height < min_dim:
                min_dim = avatar.height
            min_dim -= 1
            draw_mask.ellipse([(avatar.width / 2 - min_dim / 2, avatar.height / 2 - min_dim / 2), (avatar.width / 2 + min_dim / 2, avatar.height / 2 + min_dim / 2)], fill=255)
            avatar = Image.composite(avatar, base, mask)
            avatar = avatar.resize((int(avatar.width / min_dim * size), int(avatar.height / min_dim * size)))
            avatar.save(filepath, format=None)
            avatar.close()
            return filepath
    except NotFound:
        logging.getLogger('respobot.discord').warning(f"generate_avatar_image() failed due to: Could not find member: {discord_id} in guild {guild.id}. Using base avatar instead.")

    avatar = Image.open(env.BOT_DIRECTORY + "media/base_avatar.png")
    base = Image.new("RGBA", avatar.size, (0, 0, 0, 0))
    mask = Image.new("L", avatar.size, 0)
    draw_mask = ImageDraw.Draw(mask)
    min_dim = avatar.width
    if avatar.height < min_dim:
        min_dim = avatar.height
    min_dim -= 1
    draw_mask.ellipse([(avatar.width / 2 - min_dim / 2, avatar.height / 2 - min_dim / 2), (avatar.width / 2 + min_dim / 2, avatar.height / 2 + min_dim / 2)], fill=255)
    avatar = Image.composite(avatar, base, mask)
    avatar = avatar.resize((int(avatar.width / min_dim * size), int(avatar.height / min_dim * size)))
    avatar.save(filepath, format=None)
    avatar.close()
    return filepath


async def generate_head2head_image(guild, title, racer1_info_dict, racer1_stats_dict, racer2_info_dict, racer2_stats_dict):

    image_width = 400
    image_height = 1200
    avatar_size = image_width / 7
    font_size = image_width * 18 / 400
    im = Image.new('RGBA', (image_width, image_height), color=(0, 0, 0, 0))
    bg = Image.new('RGBA', (image_width, image_height), color=(0, 0, 0, 255))
    draw = ImageDraw.Draw(im)
    font = ImageFont.truetype(env.BOT_DIRECTORY + "media/lucon.ttf", int(font_size))
    fontBig = ImageFont.truetype(env.BOT_DIRECTORY + "media/lucon.ttf", int(font_size * 2))

    margin_v_top = 0.05 * image_width
    margin_v_bottom = 0.1 * image_width
    margin_h_right = 0.15 * image_width
    margin_h_left = 0.15 * image_width

    filepath = await generate_avatar_image(guild, racer1_info_dict['discord_id'], avatar_size)
    racer1_avatar = Image.open(filepath)
    if racer1_avatar is not None:
        x = int(image_width / 4 - racer1_avatar.width / 2)
        y = int(margin_v_top)
        im.paste(racer1_avatar, (x, y))
    x = int(image_width / 4)
    y += avatar_size + font_size
    draw.text((x, y), racer1_info_dict['name'], font=font, fill=(255, 255, 255, 255), anchor="mm")
    racer1_avatar.close()
    if os.path.exists(filepath):
        os.remove(filepath)

    filepath = await generate_avatar_image(guild, racer2_info_dict['discord_id'], avatar_size)
    racer2_avatar = Image.open(filepath)
    if racer2_avatar is not None:
        x = int(image_width * 3 / 4 - racer1_avatar.width / 2)
        y = int(margin_v_top)
        im.paste(racer2_avatar, (int(image_width * 3 / 4 - racer1_avatar.width / 2), int(margin_v_top)))
    x = int(image_width * 3 / 4)
    y += avatar_size + font_size
    draw.text((x, y), racer2_info_dict['name'], font=font, fill=(255, 255, 255, 255), anchor="mm")
    if os.path.exists(filepath):
        os.remove(filepath)

    x = int(image_width / 2)
    y = int(margin_v_top + avatar_size / 2)
    draw.text((x, y), "vs", font=fontBig, fill=(255, 255, 255, 255), anchor="mm")

    y = int(margin_v_top + avatar_size + font_size + 3 * font_size)
    draw.text((x, y), title, font=fontBig, fill=(255, 255, 255, 255), anchor="mm")

    stats_top = 2 * margin_v_top + avatar_size + 4 * font_size
    number_of_stats = 12
    stat_spacing = (image_height - stats_top - margin_v_bottom) / number_of_stats

    stat_bar_height = (0.75 * stat_spacing) - font_size
    if stat_bar_height < 3:
        stat_bar_height = 3

    if 'graph_colour' in racer1_info_dict and len(racer1_info_dict['graph_colour']) >= 4:
        racer1_colour = (racer1_info_dict['graph_colour'][0], racer1_info_dict['graph_colour'][1], racer1_info_dict['graph_colour'][2], racer1_info_dict['graph_colour'][3])
    else:
        racer1_colour = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255), 255)

    if 'graph_colour' in racer2_info_dict and len(racer2_info_dict['graph_colour']) >= 4:
        racer2_colour = (racer2_info_dict['graph_colour'][0], racer2_info_dict['graph_colour'][1], racer2_info_dict['graph_colour'][2], racer2_info_dict['graph_colour'][3])
    else:
        racer2_colour = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255), 255)

    # Draw total races
    max_scale_value = get_max_scale(racer1_stats_dict['total_races'], racer2_stats_dict['total_races'])
    max_scale_pixels = (image_width - margin_h_left - margin_h_right) / 2
    draw_head2head_bar(im, draw, font, "Total Races", stats_top, stat_spacing, max_scale_pixels, max_scale_value, racer1_stats_dict['total_races'], racer2_stats_dict['total_races'], racer1_colour, racer2_colour)

    stats_top += stat_spacing
    # Draw wins
    max_scale_value = get_max_scale(racer1_stats_dict['wins'], racer2_stats_dict['wins'])
    max_scale_pixels = (image_width - margin_h_left - margin_h_right) / 2
    draw_head2head_bar(im, draw, font, "Wins", stats_top, stat_spacing, max_scale_pixels, max_scale_value, racer1_stats_dict['wins'], racer2_stats_dict['wins'], racer1_colour, racer2_colour)

    stats_top += stat_spacing
    # Draw podiums
    max_scale_value = get_max_scale(racer1_stats_dict['podiums'], racer2_stats_dict['podiums'])
    max_scale_pixels = (image_width - margin_h_left - margin_h_right) / 2
    draw_head2head_bar(im, draw, font, "Podiums", stats_top, stat_spacing, max_scale_pixels, max_scale_value, racer1_stats_dict['podiums'], racer2_stats_dict['podiums'], racer1_colour, racer2_colour)

    stats_top += stat_spacing
    # Draw poles
    max_scale_value = get_max_scale(racer1_stats_dict['total_poles'], racer2_stats_dict['total_poles'])
    max_scale_pixels = (image_width - margin_h_left - margin_h_right) / 2
    draw_head2head_bar(im, draw, font, "Poles", stats_top, stat_spacing, max_scale_pixels, max_scale_value, racer1_stats_dict['total_poles'], racer2_stats_dict['total_poles'], racer1_colour, racer2_colour)

    stats_top += stat_spacing
    # Draw laps led
    max_scale_value = get_max_scale(racer1_stats_dict['total_laps_led'], racer2_stats_dict['total_laps_led'])
    max_scale_pixels = (image_width - margin_h_left - margin_h_right) / 2
    draw_head2head_bar(im, draw, font, "Laps Led", stats_top, stat_spacing, max_scale_pixels, max_scale_value, racer1_stats_dict['total_laps_led'], racer2_stats_dict['total_laps_led'], racer1_colour, racer2_colour)

    stats_top += stat_spacing
    # Draw avg champ points
    value1 = round(racer1_stats_dict['avg_champ_points'], 1)
    value2 = round(racer2_stats_dict['avg_champ_points'], 1)
    if value1 <= 150 and value2 <= 150:
        max_scale_value = 150
    else:
        max_scale_value = get_max_scale(value1, value2)
    max_scale_pixels = (image_width - margin_h_left - margin_h_right) / 2
    draw_head2head_bar(im, draw, font, "Average Championship Points", stats_top, stat_spacing, max_scale_pixels, max_scale_value, value1, value2, racer1_colour, racer2_colour)

    stats_top += stat_spacing
    # Draw highest champ points
    if racer1_stats_dict['highest_champ_points'] <= 150 and racer2_stats_dict['highest_champ_points'] <= 150:
        max_scale_value = 150
    else:
        max_scale_value = get_max_scale(racer1_stats_dict['highest_champ_points'], racer2_stats_dict['highest_champ_points'])
    max_scale_pixels = (image_width - margin_h_left - margin_h_right) / 2
    draw_head2head_bar(im, draw, font, "Highest Championship Points", stats_top, stat_spacing, max_scale_pixels, max_scale_value, racer1_stats_dict['highest_champ_points'], racer2_stats_dict['highest_champ_points'], racer1_colour, racer2_colour)

    stats_top += stat_spacing
    # Draw highest ir gain
    if racer1_stats_dict['highest_ir_gain'] <= 150 and racer2_stats_dict['highest_ir_gain'] <= 150:
        max_scale_value = 150
    else:
        max_scale_value = get_max_scale(racer1_stats_dict['highest_ir_gain'], racer2_stats_dict['highest_ir_gain'])

    max_scale_pixels = (image_width - margin_h_left - margin_h_right) / 2
    draw_head2head_bar(im, draw, font, "Highest iRating Gain", stats_top, stat_spacing, max_scale_pixels, max_scale_value, racer1_stats_dict['highest_ir_gain'], racer2_stats_dict['highest_ir_gain'], racer1_colour, racer2_colour)

    stats_top += stat_spacing
    # Draw highest ir
    max_scale_value = get_max_scale(racer1_stats_dict['highest_ir'], racer2_stats_dict['highest_ir'])
    max_scale_pixels = (image_width - margin_h_left - margin_h_right) / 2
    draw_head2head_bar(im, draw, font, "Highest iRating", stats_top, stat_spacing, max_scale_pixels, max_scale_value, racer1_stats_dict['highest_ir'], racer2_stats_dict['highest_ir'], racer1_colour, racer2_colour)

    stats_top += stat_spacing
    # Draw highest ir loss
    if abs(racer1_stats_dict['highest_ir_loss']) <= 150 and abs(racer2_stats_dict['highest_ir_loss']) <= 150:
        max_scale_value = 150
    else:
        max_scale_value = get_max_scale(racer1_stats_dict['highest_ir_loss'], racer2_stats_dict['highest_ir_loss'])
    max_scale_pixels = (image_width - margin_h_left - margin_h_right) / 2
    draw_head2head_bar_inverted(im, draw, font, "Highest iRating Loss", stats_top, stat_spacing, max_scale_pixels, max_scale_value, racer1_stats_dict['highest_ir_loss'], racer2_stats_dict['highest_ir_loss'], racer1_colour, racer2_colour)

    stats_top += stat_spacing
    # Draw lowest ir
    max_scale_value = get_max_scale(racer1_stats_dict['lowest_ir'], racer2_stats_dict['lowest_ir'])
    max_scale_pixels = (image_width - margin_h_left - margin_h_right) / 2
    draw_head2head_bar(im, draw, font, "Lowest iRating", stats_top, stat_spacing, max_scale_pixels, max_scale_value, racer1_stats_dict['lowest_ir'], racer2_stats_dict['lowest_ir'], racer1_colour, racer2_colour)

    stats_top += stat_spacing
    # Draw laps_per_incident
    value1 = round(racer1_stats_dict['laps_per_inc'], 1)
    value2 = round(racer2_stats_dict['laps_per_inc'], 1)
    max_scale_value = get_max_scale(value1, value2)
    max_scale_pixels = (image_width - margin_h_left - margin_h_right) / 2
    draw_head2head_bar(im, draw, font, "Laps Per Incident", stats_top, stat_spacing, max_scale_pixels, max_scale_value, value1, value2, racer1_colour, racer2_colour)

    im = Image.alpha_composite(bg, im)
    return im


def generate_champ_graph(data_dict, title, weeks_to_count, ongoing):

    to_delete = []

    for member in data_dict:
        if len(data_dict[member]['weeks']) < 1:
            to_delete.append(member)

    for member in to_delete:
        del data_dict[member]

    data_dict = dict(sorted(data_dict.items(), key=lambda item: item[1]['total_points'], reverse=True))

    font = ImageFont.truetype(env.BOT_DIRECTORY + "media/lucon.ttf", 18)

    margin_v_top = 3 * font.size
    margin_v_bottom = font.size
    margin_h_right = font.size
    margin_h_left = font.size

    name_width = 0

    for member in data_dict:
        (left, top, right, bottom) = font.getbbox(member)
        if (right - left) > name_width:
            name_width = (right - left)

    row_height = 2 * font.size
    image_height = margin_v_top + row_height * (len(data_dict) + 1) + margin_v_bottom

    name_width += font.size
    (left, top, right, bottom) = font.getbbox("Wk 12")
    week_width = (right - left) + font.size

    (left, top, right, bottom) = font.getbbox("Total")
    total_width = (right - left) + font.size

    (left, top, right, bottom) = font.getbbox("Potential")
    projected_width = (right - left) + font.size

    table_width = name_width + 12 * week_width + total_width

    if ongoing is True:
        table_width += projected_width

    image_width = margin_h_left + table_width + margin_h_right

    im = Image.new('RGBA', (image_width, image_height), color=(0, 0, 0, 0))
    bg = Image.new('RGBA', (image_width, image_height), color=(0, 0, 0, 255))
    draw = ImageDraw.Draw(im)

    # Draw the title
    draw.text((image_width * 0.5, margin_v_top * 0.5), title, font=font, fill=(255, 255, 255, 255), anchor="mm")

    # Draw the headers
    x = int(margin_h_left)
    y = int(margin_v_top + row_height / 2)
    draw.text((x + font.size, y), "Name", font=font, fill=(255, 255, 255, 255), anchor="lm")

    x += int(name_width + week_width / 2)
    for i in range(0, 12):
        draw.text((x, y), "wk" + str(i + 1), font=font, fill=(255, 255, 255, 255), anchor="mm")
        x += int(week_width)

    x += int(total_width / 2 - week_width / 2)
    draw.text((x, y), "Total", font=font, fill=(255, 255, 255, 255), anchor="mm")

    if ongoing is True:
        x += int(total_width / 2 + projected_width / 2)
        draw.text((x, y), "Potential", font=font, fill=(255, 255, 255, 255), anchor="mm")

    draw.line([(margin_h_left, margin_v_top + row_height), (margin_h_left + table_width, margin_v_top + row_height)], fill=(255, 255, 255, 255), width=1, joint=None)

    # Draw the members details
    members_drawn = 0

    for member in data_dict:
        x = int(margin_h_left)
        y = int(margin_v_top + row_height + row_height * members_drawn + row_height / 2)
        if members_drawn % 2 == 1:
            draw.rectangle([(margin_h_left, int(y - row_height / 2)), (margin_h_left + table_width, int(y + row_height / 2))], fill=(24, 24, 24, 255))
        draw.text((x + font.size, y), member, font=font, fill=(255, 255, 255, 255), anchor="lm")
        x += int(name_width + week_width / 2)
        weeks_drawn = 0
        for week in data_dict[member]['weeks']:
            if weeks_drawn < weeks_to_count:
                colour = (0, 128, 255, 255)
            else:
                colour = (112, 112, 112, 255)

            draw.text((int(x + int(week) * week_width), y), str(data_dict[member]['weeks'][week]), font=font, fill=colour, anchor="mm")

            weeks_drawn += 1

        x = int(margin_h_left + name_width + 12 * week_width)
        draw.text((x + total_width / 2, y), str(data_dict[member]['total_points']), font=font, fill=(192, 0, 0, 255), anchor="mm")
        if ongoing is True:
            x = int(margin_h_left + name_width + 12 * week_width + total_width)
            draw.text((x + projected_width / 2, y), str(data_dict[member]['projected_points']), font=font, fill=(192, 64, 0, 255), anchor="mm")
        members_drawn += 1

    im = Image.alpha_composite(bg, im)
    return im


def generate_champ_graph_compact(data_dict, title, weeks_to_count, highlighted_week):

    to_delete = []

    for member in data_dict:
        if len(data_dict[member]['weeks']) < 1:
            to_delete.append(member)

    for member in to_delete:
        del data_dict[member]

    data_dict = dict(sorted(data_dict.items(), key=lambda item: item[1]['total_points'], reverse=True))

    font = ImageFont.truetype(env.BOT_DIRECTORY + "media/lucon.ttf", 18)

    margin_v_top = 3 * font.size
    margin_v_bottom = font.size
    margin_h_right = font.size
    margin_h_left = font.size

    name_width = 0

    for member in data_dict:
        (left, top, right, bottom) = font.getbbox(member)
        if (right - left) > name_width:
            name_width = (right - left)

    row_height = 2 * font.size

    name_width += font.size

    (left, top, right, bottom) = font.getbbox("Wk 12")
    week_width = (right - left) + font.size

    (left, top, right, bottom) = font.getbbox("Total")
    total_width = (right - left) + font.size

    table_width = name_width + week_width + total_width

    image_width = margin_h_left + table_width + margin_h_right

    # Chop the title up into separate lines
    title_words = title.split()
    title_lines = []
    i = 0
    title_line_count = 0
    title_line = ""
    title_done = False
    while not title_done:
        width = 0
        if i < len(title_words):
            (left, top, right, bottom) = font.getbbox(title_line + title_words[i])
            width = right - left
        else:
            title_done = True

        if title_done or width >= image_width - margin_h_left - margin_h_right:
            title_lines.append(title_line[:-1])
            title_line_count += 1
            title_line = ""
        else:
            title_line += title_words[i] + " "
            i += 1

    title_line_count -= 1

    image_height = int(margin_v_top + title_line_count * font.size * 1.5 + row_height * (len(data_dict) + 1) + margin_v_bottom)

    im = Image.new('RGBA', (image_width, image_height), color=(0, 0, 0, 0))
    bg = Image.new('RGBA', (image_width, image_height), color=(0, 0, 0, 255))
    draw = ImageDraw.Draw(im)

    y = int(margin_v_top * 0.5)
    # Draw the title
    for title_line in title_lines:
        draw.text((image_width * 0.5, y), title_line, font=font, fill=(255, 255, 255, 255), anchor="mm")
        y += int(font.size * 1.5)

    # Draw the headers
    x = int(margin_h_left)
    y = int(margin_v_top + title_line_count * font.size * 1.5 + row_height / 2)
    draw.text((x + font.size, y), "Name", font=font, fill=(255, 255, 255, 255), anchor="lm")

    x += int(name_width + week_width / 2)
    draw.text((x, y), "wk" + str(highlighted_week), font=font, fill=(255, 255, 255, 255), anchor="mm")

    x += int(total_width / 2 + week_width / 2)
    draw.text((x, y), "Total", font=font, fill=(255, 255, 255, 255), anchor="mm")

    draw.line([(margin_h_left, margin_v_top + title_line_count * font.size * 1.5 + row_height), (margin_h_left + table_width, margin_v_top + title_line_count * font.size * 1.5 + row_height)], fill=(255, 255, 255, 255), width=1, joint=None)

    # Draw the members details
    members_drawn = 0

    for member in data_dict:
        x = int(margin_h_left)
        y = int(margin_v_top + title_line_count * font.size * 1.5 + row_height + row_height * members_drawn + row_height / 2)
        if members_drawn % 2 == 1:
            draw.rectangle([(margin_h_left, int(y - row_height / 2)), (margin_h_left + table_width, int(y + row_height / 2))], fill=(24, 24, 24, 255))
        draw.text((x + font.size, y), member, font=font, fill=(255, 255, 255, 255), anchor="lm")

        weeks_counted = 0
        colour = (112, 112, 112, 255)
        for week in data_dict[member]['weeks']:
            if weeks_counted < weeks_to_count and int(week) == highlighted_week - 1:
                colour = (0, 128, 255, 255)
            weeks_counted += 1

        x += int(name_width + week_width / 2)
        if str(highlighted_week - 1) in data_dict[member]['weeks']:
            points = data_dict[member]['weeks'][str(highlighted_week - 1)]
            draw.text((x, y), str(points), font=font, fill=colour, anchor="mm")

        x += int(week_width / 2 + total_width / 2)
        draw.text((x, y), str(data_dict[member]['total_points']), font=font, fill=(192, 0, 0, 255), anchor="mm")
        members_drawn += 1

    im = Image.alpha_composite(bg, im)
    return im


def get_max_scale(value1, value2):
    max_value = abs(value1)
    if abs(value2) > abs(value1):
        max_value = abs(value2)

    possible_max_scales = [5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 50000, 100000, 200000, 500000, 1000000]

    for scale in possible_max_scales:
        if scale >= max_value:
            return scale


def draw_head2head_bar(im, draw, font, label, v_pos, height, max_scale_pixels, max_scale_value, racer1_value, racer2_value, racer1_colour, racer2_colour):
    draw.text((im.width * 0.5, v_pos + 2 * font.size), label, font=font, fill=(255, 255, 255, 255), anchor="mm")

    # Racer1
    if abs(racer1_value) > 0:
        left = im.width / 2 - max_scale_pixels * (racer1_value / max_scale_value)
    else:
        left = im.width / 2 - font.size / 4
    right = im.width / 2
    bottom = v_pos + height

    bar_height = height - 3 * font.size

    draw.rectangle([(left, bottom - bar_height), (right, bottom)], fill=racer1_colour)
    draw.text((left - font.size / 2, bottom - bar_height / 2), str(racer1_value), font=font, fill=(255, 255, 255, 255), anchor="rm")

    # Racer2
    if abs(racer2_value) > 0:
        right = im.width / 2 + max_scale_pixels * (racer2_value / max_scale_value)
    else:
        right = im.width / 2 + font.size / 4
    left = im.width / 2

    draw.rectangle([(left, bottom - bar_height), (right, bottom)], fill=racer2_colour)
    draw.text((right + font.size / 2, bottom - bar_height / 2), str(racer2_value), font=font, fill=(255, 255, 255, 255), anchor="lm")


def draw_head2head_bar_inverted(im, draw, font, label, v_pos, height, max_scale_pixels, max_scale_value, racer1_value, racer2_value, racer1_colour, racer2_colour):
    draw.text((im.width * 0.5, v_pos + 2 * font.size), label, font=font, fill=(255, 255, 255, 255), anchor="mm")

    # Racer1
    if abs(racer1_value) > 0:
        left = im.width / 2 - max_scale_pixels * abs(abs(racer1_value) - abs(max_scale_value)) / max_scale_value
    else:
        left = im.width / 2 - font.size / 4
    right = im.width / 2
    bottom = v_pos + height

    bar_height = height - 3 * font.size

    draw.rectangle([(left, bottom - bar_height), (right, bottom)], fill=racer1_colour)
    draw.text((left - font.size / 2, bottom - bar_height / 2), str(racer1_value), font=font, fill=(255, 255, 255, 255), anchor="rm")

    # Racer2
    if abs(racer2_value) > 0:
        right = im.width / 2 + max_scale_pixels * abs(abs(racer2_value) - abs(max_scale_value)) / max_scale_value
    else:
        right = im.width / 2 + font.size / 4
    left = im.width / 2

    draw.rectangle([(left, bottom - bar_height), (right, bottom)], fill=racer2_colour)
    draw.text((right + font.size / 2, bottom - bar_height / 2), str(racer2_value), font=font, fill=(255, 255, 255, 255), anchor="lm")


def generate_ir_graph(member_dicts, title, print_legend):
    image_width = 1000
    image_height = 320
    im = Image.new('RGBA', (image_width, image_height), color=(0, 0, 0, 0))
    bg = Image.new('RGBA', (image_width, image_height), color=(0, 0, 0, 255))
    draw = ImageDraw.Draw(im)
    font = ImageFont.truetype(env.BOT_DIRECTORY + "media/lucon.ttf", int(image_height * 16 / 300))
    fontsm = ImageFont.truetype(env.BOT_DIRECTORY + "media/lucon.ttf", int(image_height * 12 / 300))

    margin_v_top = 0.15 * image_height
    margin_v_bottom = 0.15 * image_height

    if print_legend:
        margin_h_right = 0.27 * image_width
    else:
        margin_h_right = 0.15 * image_height

    margin_h_left = 0.08 * image_width

    tick_length = 0.05 * image_height

    # Draw the title
    draw.text((image_width * 0.5, margin_v_top * 0.5), title, font=font, fill=(255, 255, 255, 255), anchor="mm")

    max_ir = 0
    min_timestamp = 10000000000000

    for member_dict in member_dicts:
        for point in member_dict['ir_data']:
            if point[1] > max_ir:
                max_ir = point[1]
            if point[0] < min_timestamp:
                min_timestamp = point[0]

    ir_scale_maj_division_size = math.ceil((max_ir / 8) / 500) * 500
    if ir_scale_maj_division_size > 1000:
        ir_scale_maj_division_size = math.ceil(ir_scale_maj_division_size / 1000) * 1000
    ir_scale_maj_divisions = math.ceil(max_ir / ir_scale_maj_division_size)
    ir_scale_pixels = (image_height - margin_v_bottom - margin_v_top)
    pleb_line_drawn = False

    max_timestamp = int(datetime.now().timestamp() * 1000)

    timestamp_range = max_timestamp - min_timestamp
    timestamp_range_pixels = image_width - margin_h_right - margin_h_left

    earliest_datetime = date.fromtimestamp(min_timestamp / 1000)
    latest_datetime = date.fromtimestamp(max_timestamp / 1000)

    earliest_year = earliest_datetime.year
    latest_year = latest_datetime.year

    dates = []

    for i in range(earliest_year + 1, latest_year + 1):
        dates.append(datetime(i, 1, 1))

    for day in dates:
        year_timestamp = int(day.timestamp()) * 1000
        x = margin_h_left + (year_timestamp - min_timestamp) / timestamp_range * timestamp_range_pixels
        y = image_height - margin_v_bottom
        draw.line([(x, y + tick_length / 2), (x, y)], fill=(255, 255, 255, 255), width=1, joint=None)
        if len(dates) < 6:
            draw.text((x, y + tick_length), str(day.year) + "-1-1", font=font, fill=(255, 255, 255, 255), anchor="mt")
        else:
            draw.text((x, y + tick_length), str(day.year), font=font, fill=(255, 255, 255, 255), anchor="mt")

    for i in range(1, ir_scale_maj_divisions + 1):
        x = margin_h_left
        y = image_height - margin_v_bottom - i * ir_scale_pixels / ir_scale_maj_divisions
        if int(i * ir_scale_maj_division_size) != constants.pleb_line:
            draw.line([(x, y), (image_width - margin_h_right, y)], fill=(255, 255, 255, 64), width=1, joint=None)
            draw.text((x - tick_length / 2, y), str(i * ir_scale_maj_division_size), font=font, fill=(255, 255, 255, 255), anchor="rm")
        else:
            draw.line([(x, y), (image_width - margin_h_right, y)], fill=(255, 0, 0, 128), width=1, joint=None)
            draw.text((x - tick_length / 2, y), str("Pleb\nLine"), font=font, fill=(255, 255, 255, 255), anchor="rm")
            pleb_line_drawn = True
    if not pleb_line_drawn:
        x = margin_h_left
        y = image_height - margin_v_bottom - constants.pleb_line / (ir_scale_maj_divisions * ir_scale_maj_division_size) * ir_scale_pixels
        draw.line([(x, y), (image_width - margin_h_right, y)], fill=(255, 0, 0, 128), width=1, joint=None)
        draw.text((x - tick_length / 2, y), str("Pleb Line"), font=fontsm, fill=(255, 0, 0, 128), anchor="rm")

    scaled_tuples = []

    count = 0

    legend_v_spacing = ir_scale_pixels / 10
    box_size = legend_v_spacing * 0.75

    for member_dict in member_dicts:
        scaled_tuples.append([])
        colour = (member_dict['graph_colour'][0], member_dict['graph_colour'][1], member_dict['graph_colour'][2], member_dict['graph_colour'][3])

        if len(member_dict['name']) < 16:
            legend_name = member_dict['name']
        else:
            legend_name = member_dict['name'][0:11] + "..."

        legend_ir_text = " (" + str(member_dict['ir_data'][-1][1]) + ")"

        for i in range(0, 22 - len(legend_name) - len(legend_ir_text)):
            legend_name += " "

        legend_name += legend_ir_text

        for point in member_dict['ir_data']:
            scaled_tuples[count].append((margin_h_left + (point[0] - min_timestamp) / timestamp_range * timestamp_range_pixels, image_height - margin_v_bottom - point[1] / (ir_scale_maj_divisions * ir_scale_maj_division_size) * ir_scale_pixels))
        draw.line(scaled_tuples[count], fill=colour, width=2, joint="curve")
        x = image_width - margin_h_right + tick_length
        y = margin_v_top + legend_v_spacing * 0.5 - box_size / 2 + count * legend_v_spacing

        if print_legend:
            draw.rectangle([(x, y), (x + box_size, y + box_size)], fill=colour, outline=(255, 255, 255, 255), width=1)
            draw.text((x + box_size * 1.5, y + box_size / 2), legend_name, font=font, fill=(255, 255, 255, 255), anchor="lm")

        count += 1

    # Draw the axes
    draw.line([(margin_h_left, image_height - margin_v_bottom), (image_width - margin_h_right, image_height - margin_v_bottom)], fill=(255, 255, 255, 255), width=2, joint=None)
    draw.line([(margin_h_left, image_height - margin_v_bottom), (margin_h_left, margin_v_top)], fill=(255, 255, 255, 255), width=2, joint=None)

    im = Image.alpha_composite(bg, im)
    return im

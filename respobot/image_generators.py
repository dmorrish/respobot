import io
import math
import random
import environment_variables as env
import constants
import logging
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, date, timezone, timedelta
from discord.errors import NotFound


async def generate_guild_icon(angle):
    icon = Image.open(env.BOT_DIRECTORY + env.MEDIA_SUBDIRECTORY + constants.GUILD_ICON_FILENAME)
    icon = icon.rotate(angle, resample=Image.BICUBIC)
    return icon


async def generate_compass_image(guild, compass_data, time_span_text):
    image_width = 600
    image_height = 600
    avatar_size = 25
    font_size = image_width * 18 / 600
    bg = Image.new('RGBA', (image_width, image_height), color=(0, 0, 0, 255))
    font = ImageFont.truetype(
        env.BOT_DIRECTORY + env.MEDIA_SUBDIRECTORY + constants.IMAGE_FONT_FILENAME,
        int(font_size)
    )
    fontBig = ImageFont.truetype(
        env.BOT_DIRECTORY + env.MEDIA_SUBDIRECTORY + constants.IMAGE_FONT_FILENAME,
        int(font_size * 2)
    )

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
        y = (
            image_height
            - margin_v_bottom
            - margin_axis_label
            - (tick_number - int(pts_scale_min / 10)) * pixels_per_tick
        )
        draw.line([(x, y), (x - tick_length, y)], fill=(255, 255, 255, 255), width=1, joint=None)
        draw.text((x - tick_length * 2, y), str(tick_number * 10), font=font, fill=(255, 255, 255, 255), anchor="rm")

    bg = Image.alpha_composite(bg, im)

    laps_per_inc_scale = graph_width / (laps_per_inc_scale_max - laps_per_inc_scale_min)
    avg_champ_points_scale = graph_height / (pts_scale_max - pts_scale_min)

    for member in compass_data:
        compass_data[member]['point'] = (
            int(
                (compass_data[member]['point'][0] - laps_per_inc_scale_min)
                * laps_per_inc_scale + margin_h_left + margin_axis_label - avatar_size / 2
            ),
            int(
                image_height - margin_v_bottom - margin_axis_label - (avatar_size / 2)
                - (compass_data[member]['point'][1] - pts_scale_min) * avg_champ_points_scale
            )
        )
        avatar = await generate_avatar_image(guild, compass_data[member]['discordID'], avatar_size)
        im = Image.new('RGBA', (image_width, image_height), color=(0, 0, 0, 0))
        im.paste(avatar, compass_data[member]['point'])
        bg = Image.alpha_composite(bg, im)
        avatar.close()

    im = Image.new('RGBA', (image_width, image_height), color=(0, 0, 0, 0))
    draw = ImageDraw.Draw(im)

    # Draw the title
    draw.text(
        (image_width * 0.5, margin_v_top + margin_title * 0.333),
        "r/RespoCompassMemes",
        font=fontBig,
        fill=(255, 255, 255, 255),
        anchor="mm"
    )
    draw.text(
        (image_width * 0.5, margin_v_top + margin_title * 0.666),
        time_span_text,
        font=font,
        fill=(255, 255, 255, 255),
        anchor="mm"
    )

    # Draw chart axes
    draw.line(
        [
            (margin_h_left + margin_axis_label, image_height - margin_v_bottom - margin_axis_label),
            (image_width - margin_h_right, image_height - margin_v_bottom - margin_axis_label)
        ],
        fill=(255, 255, 255, 255),
        width=2,
        joint=None
    )
    draw.line(
        [
            (margin_h_left + margin_axis_label, image_height - margin_v_bottom - margin_axis_label),
            (margin_h_left + margin_axis_label, margin_v_top + margin_title)
        ],
        fill=(255, 255, 255, 255),
        width=2,
        joint=None
    )

    draw.text(
        (margin_h_left + margin_axis_label + graph_width / 2, image_height - margin_axis_label / 2),
        "Laps Per Incident",
        font=font,
        fill=(255, 255, 255, 255),
        anchor="mm"
    )

    # Text to be rotated...
    rotate_text = u'Average Championship Points'

    # Image for text to be rotated
    (left, top, right, bottom) = font.getbbox(rotate_text)
    img_txt = Image.new('L', (right - left, bottom - top))
    draw_txt = ImageDraw.Draw(img_txt)
    draw_txt.text((0, 0), rotate_text, font=font, fill=255)
    t = img_txt.rotate(90, expand=1)
    im.paste(
        t,
        (
            int(margin_axis_label / 2 - t.width / 2),
            int(image_height - margin_v_bottom - margin_axis_label - graph_height / 2 - t.height / 2)
        )
    )

    bg = Image.alpha_composite(bg, im)

    return bg


async def generate_avatar_image(guild, discord_id, size, is_smurf=False):

    avatar_memory_file = io.BytesIO()
    if guild is not None and discord_id is not None and discord_id > 0 and is_smurf is False:
        try:
            member_obj = await guild.fetch_member(discord_id)
            if member_obj and member_obj.display_avatar is not None:
                await member_obj.display_avatar.save(avatar_memory_file)
                avatar_memory_file.seek(0)
                avatar = Image.open(avatar_memory_file)
                base = Image.new("RGBA", avatar.size, (0, 0, 0, 0))
                mask = Image.new("L", avatar.size, 0)
                draw_mask = ImageDraw.Draw(mask)
                min_dim = avatar.width
                if avatar.height < min_dim:
                    min_dim = avatar.height
                min_dim -= 1
                draw_mask.ellipse(
                    [
                        (avatar.width / 2 - min_dim / 2, avatar.height / 2 - min_dim / 2),
                        (avatar.width / 2 + min_dim / 2, avatar.height / 2 + min_dim / 2)
                    ],
                    fill=255
                )
                avatar = Image.composite(avatar, base, mask)
                avatar = avatar.resize((int(avatar.width / min_dim * size), int(avatar.height / min_dim * size)))
                return avatar
        except NotFound:
            logging.getLogger('respobot.discord').warning(
                f"generate_avatar_image() failed due to: Could not find member: {discord_id} in "
                f"guild {guild.id}. Using base avatar instead."
            )

    if is_smurf is True:
        avatar = Image.open(env.BOT_DIRECTORY + env.MEDIA_SUBDIRECTORY + constants.SMURF_AVATAR_FILENAME)
    elif discord_id is not None and discord_id > 0:
        avatar = Image.open(env.BOT_DIRECTORY + env.MEDIA_SUBDIRECTORY + constants.BASE_AVATAR_FILENAME)
    else:
        avatar = Image.open(env.BOT_DIRECTORY + env.MEDIA_SUBDIRECTORY + constants.RESPO_LOGO_FILENAME)
    base = Image.new("RGBA", avatar.size, (0, 0, 0, 0))
    mask = Image.new("L", avatar.size, 0)
    draw_mask = ImageDraw.Draw(mask)
    min_dim = avatar.width
    if avatar.height < min_dim:
        min_dim = avatar.height
    min_dim -= 1
    draw_mask.ellipse(
        [
            (avatar.width / 2 - min_dim / 2, avatar.height / 2 - min_dim / 2),
            (avatar.width / 2 + min_dim / 2, avatar.height / 2 + min_dim / 2)
        ],
        fill=255
    )
    avatar = Image.composite(avatar, base, mask)
    avatar = avatar.resize((int(avatar.width / min_dim * size), int(avatar.height / min_dim * size)))
    avatar_memory_file.close()
    return avatar


async def generate_head2head_image(
    guild,
    title,
    racer1_info_dict,
    racer1_stats_dict,
    racer2_info_dict,
    racer2_stats_dict
):

    image_width = 400
    image_height = 1200
    avatar_size = image_width / 7
    font_size = image_width * 18 / 400
    im = Image.new('RGBA', (image_width, image_height), color=(0, 0, 0, 0))
    bg = Image.new('RGBA', (image_width, image_height), color=(0, 0, 0, 255))
    draw = ImageDraw.Draw(im)
    font = ImageFont.truetype(
        env.BOT_DIRECTORY + env.MEDIA_SUBDIRECTORY + constants.IMAGE_FONT_FILENAME,
        int(font_size)
    )
    fontBig = ImageFont.truetype(
        env.BOT_DIRECTORY + env.MEDIA_SUBDIRECTORY + constants.IMAGE_FONT_FILENAME,
        int(font_size * 2)
    )

    margin_v_top = 0.05 * image_width
    margin_v_bottom = 0.1 * image_width
    margin_h_right = 0.15 * image_width
    margin_h_left = 0.15 * image_width

    racer1_avatar = await generate_avatar_image(
        guild,
        racer1_info_dict['discord_id'],
        avatar_size,
        racer1_info_dict['is_smurf'] == 1
    )
    if racer1_avatar is not None:
        x = int(image_width / 4 - racer1_avatar.width / 2)
        y = int(margin_v_top)
        im.paste(racer1_avatar, (x, y))
    x = int(image_width / 4)
    y += avatar_size + font_size
    draw.text((x, y), racer1_info_dict['name'], font=font, fill=(255, 255, 255, 255), anchor="mm")
    racer1_avatar.close()

    racer2_avatar = await generate_avatar_image(
        guild,
        racer2_info_dict['discord_id'],
        avatar_size,
        racer2_info_dict['is_smurf'] == 1
    )
    if racer2_avatar is not None:
        x = int(image_width * 3 / 4 - racer1_avatar.width / 2)
        y = int(margin_v_top)
        im.paste(racer2_avatar, (int(image_width * 3 / 4 - racer1_avatar.width / 2), int(margin_v_top)))
    x = int(image_width * 3 / 4)
    y += avatar_size + font_size
    draw.text((x, y), racer2_info_dict['name'], font=font, fill=(255, 255, 255, 255), anchor="mm")

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

    if (
        'graph_colour' in racer1_info_dict
        and racer1_info_dict['graph_colour'] is not None
        and len(racer1_info_dict['graph_colour']) >= 4
    ):
        racer1_colour = (
            racer1_info_dict['graph_colour'][0],
            racer1_info_dict['graph_colour'][1],
            racer1_info_dict['graph_colour'][2],
            racer1_info_dict['graph_colour'][3]
        )
    else:
        racer1_colour = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255), 255)

    if (
        'graph_colour' in racer2_info_dict
        and racer2_info_dict['graph_colour'] is not None
        and len(racer2_info_dict['graph_colour']) >= 4
    ):
        racer2_colour = (
            racer2_info_dict['graph_colour'][0],
            racer2_info_dict['graph_colour'][1],
            racer2_info_dict['graph_colour'][2],
            racer2_info_dict['graph_colour'][3]
        )
    else:
        racer2_colour = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255), 255)

    # Draw total races
    max_scale_value = get_max_scale(racer1_stats_dict['total_races'], racer2_stats_dict['total_races'])
    max_scale_pixels = (image_width - margin_h_left - margin_h_right) / 2
    draw_head2head_bar(
        im,
        draw,
        font,
        "Total Races",
        stats_top,
        stat_spacing,
        max_scale_pixels,
        max_scale_value,
        racer1_stats_dict['total_races'],
        racer2_stats_dict['total_races'],
        racer1_colour, racer2_colour
    )

    stats_top += stat_spacing
    # Draw wins
    max_scale_value = get_max_scale(racer1_stats_dict['wins'], racer2_stats_dict['wins'])
    max_scale_pixels = (image_width - margin_h_left - margin_h_right) / 2
    draw_head2head_bar(
        im,
        draw,
        font,
        "Wins",
        stats_top,
        stat_spacing,
        max_scale_pixels,
        max_scale_value,
        racer1_stats_dict['wins'],
        racer2_stats_dict['wins'],
        racer1_colour, racer2_colour
    )

    stats_top += stat_spacing
    # Draw podiums
    max_scale_value = get_max_scale(racer1_stats_dict['podiums'], racer2_stats_dict['podiums'])
    max_scale_pixels = (image_width - margin_h_left - margin_h_right) / 2
    draw_head2head_bar(
        im,
        draw,
        font,
        "Podiums",
        stats_top,
        stat_spacing,
        max_scale_pixels,
        max_scale_value,
        racer1_stats_dict['podiums'],
        racer2_stats_dict['podiums'],
        racer1_colour, racer2_colour
    )

    stats_top += stat_spacing
    # Draw poles
    max_scale_value = get_max_scale(racer1_stats_dict['total_poles'], racer2_stats_dict['total_poles'])
    max_scale_pixels = (image_width - margin_h_left - margin_h_right) / 2
    draw_head2head_bar(
        im,
        draw,
        font,
        "Poles",
        stats_top,
        stat_spacing,
        max_scale_pixels,
        max_scale_value,
        racer1_stats_dict['total_poles'],
        racer2_stats_dict['total_poles'],
        racer1_colour, racer2_colour
    )

    stats_top += stat_spacing
    # Draw laps led
    max_scale_value = get_max_scale(racer1_stats_dict['total_laps_led'], racer2_stats_dict['total_laps_led'])
    max_scale_pixels = (image_width - margin_h_left - margin_h_right) / 2
    draw_head2head_bar(
        im,
        draw,
        font,
        "Laps Led",
        stats_top,
        stat_spacing,
        max_scale_pixels,
        max_scale_value,
        racer1_stats_dict['total_laps_led'],
        racer2_stats_dict['total_laps_led'],
        racer1_colour, racer2_colour
    )

    stats_top += stat_spacing
    # Draw avg champ points
    value1 = round(racer1_stats_dict['avg_champ_points'], 1)
    value2 = round(racer2_stats_dict['avg_champ_points'], 1)
    if value1 <= 150 and value2 <= 150:
        max_scale_value = 150
    else:
        max_scale_value = get_max_scale(value1, value2)
    max_scale_pixels = (image_width - margin_h_left - margin_h_right) / 2
    draw_head2head_bar(
        im,
        draw,
        font,
        "Average Championship Points",
        stats_top,
        stat_spacing,
        max_scale_pixels,
        max_scale_value,
        value1, value2,
        racer1_colour, racer2_colour
    )

    stats_top += stat_spacing
    # Draw highest champ points
    if racer1_stats_dict['highest_champ_points'] <= 150 and racer2_stats_dict['highest_champ_points'] <= 150:
        max_scale_value = 150
    else:
        max_scale_value = get_max_scale(
            racer1_stats_dict['highest_champ_points'],
            racer2_stats_dict['highest_champ_points']
        )
    max_scale_pixels = (image_width - margin_h_left - margin_h_right) / 2
    draw_head2head_bar(
        im,
        draw,
        font,
        "Highest Championship Points",
        stats_top,
        stat_spacing,
        max_scale_pixels,
        max_scale_value,
        racer1_stats_dict['highest_champ_points'],
        racer2_stats_dict['highest_champ_points'],
        racer1_colour, racer2_colour
    )

    stats_top += stat_spacing
    # Draw highest ir gain
    if racer1_stats_dict['highest_ir_gain'] <= 150 and racer2_stats_dict['highest_ir_gain'] <= 150:
        max_scale_value = 150
    else:
        max_scale_value = get_max_scale(racer1_stats_dict['highest_ir_gain'], racer2_stats_dict['highest_ir_gain'])

    max_scale_pixels = (image_width - margin_h_left - margin_h_right) / 2
    draw_head2head_bar(
        im,
        draw,
        font,
        "Highest iRating Gain",
        stats_top,
        stat_spacing,
        max_scale_pixels,
        max_scale_value,
        racer1_stats_dict['highest_ir_gain'],
        racer2_stats_dict['highest_ir_gain'],
        racer1_colour, racer2_colour
    )

    stats_top += stat_spacing
    # Draw highest ir
    max_scale_value = get_max_scale(racer1_stats_dict['highest_ir'], racer2_stats_dict['highest_ir'])
    max_scale_pixels = (image_width - margin_h_left - margin_h_right) / 2
    draw_head2head_bar(
        im,
        draw,
        font,
        "Highest iRating",
        stats_top,
        stat_spacing,
        max_scale_pixels,
        max_scale_value,
        racer1_stats_dict['highest_ir'],
        racer2_stats_dict['highest_ir'],
        racer1_colour, racer2_colour
    )

    stats_top += stat_spacing
    # Draw highest ir loss
    if abs(racer1_stats_dict['highest_ir_loss']) <= 150 and abs(racer2_stats_dict['highest_ir_loss']) <= 150:
        max_scale_value = 150
    else:
        max_scale_value = get_max_scale(racer1_stats_dict['highest_ir_loss'], racer2_stats_dict['highest_ir_loss'])
    max_scale_pixels = (image_width - margin_h_left - margin_h_right) / 2
    draw_head2head_bar_inverted(
        im,
        draw,
        font,
        "Highest iRating Loss",
        stats_top, stat_spacing,
        max_scale_pixels,
        max_scale_value,
        racer1_stats_dict['highest_ir_loss'],
        racer2_stats_dict['highest_ir_loss'],
        racer1_colour, racer2_colour
    )

    stats_top += stat_spacing
    # Draw lowest ir
    max_scale_value = get_max_scale(racer1_stats_dict['lowest_ir'], racer2_stats_dict['lowest_ir'])
    max_scale_pixels = (image_width - margin_h_left - margin_h_right) / 2
    draw_head2head_bar(
        im,
        draw,
        font,
        "Lowest iRating",
        stats_top,
        stat_spacing,
        max_scale_pixels,
        max_scale_value,
        racer1_stats_dict['lowest_ir'],
        racer2_stats_dict['lowest_ir'],
        racer1_colour, racer2_colour
    )

    stats_top += stat_spacing
    # Draw laps_per_incident
    value1 = round(racer1_stats_dict['laps_per_inc'], 1)
    value2 = round(racer2_stats_dict['laps_per_inc'], 1)
    max_scale_value = get_max_scale(value1, value2)
    max_scale_pixels = (image_width - margin_h_left - margin_h_right) / 2
    draw_head2head_bar(
        im,
        draw,
        font,
        "Laps Per Incident",
        stats_top,
        stat_spacing,
        max_scale_pixels,
        max_scale_value,
        value1,
        value2,
        racer1_colour,
        racer2_colour
    )

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

    font = ImageFont.truetype(env.BOT_DIRECTORY + env.MEDIA_SUBDIRECTORY + constants.IMAGE_FONT_FILENAME, 18)

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

    draw.line(
        [
            (margin_h_left, margin_v_top + row_height),
            (margin_h_left + table_width, margin_v_top + row_height)
        ],
        fill=(255, 255, 255, 255),
        width=1,
        joint=None
    )

    # Draw the members details
    members_drawn = 0

    for member in data_dict:
        x = int(margin_h_left)
        y = int(margin_v_top + row_height + row_height * members_drawn + row_height / 2)
        if members_drawn % 2 == 1:
            draw.rectangle(
                [
                    (margin_h_left, int(y - row_height / 2)),
                    (margin_h_left + table_width, int(y + row_height / 2))
                ],
                fill=(24, 24, 24, 255)
            )
        draw.text((x + font.size, y), member, font=font, fill=(255, 255, 255, 255), anchor="lm")
        x += int(name_width + week_width / 2)
        weeks_drawn = 0
        for week in data_dict[member]['weeks']:
            if weeks_drawn < weeks_to_count:
                colour = (0, 128, 255, 255)
            else:
                colour = (112, 112, 112, 255)

            draw.text(
                (int(x + int(week) * week_width), y),
                str(data_dict[member]['weeks'][week]),
                font=font,
                fill=colour, anchor="mm"
            )

            weeks_drawn += 1

        x = int(margin_h_left + name_width + 12 * week_width)
        draw.text(
            (x + total_width / 2, y),
            str(data_dict[member]['total_points']),
            font=font,
            fill=(192, 0, 0, 255),
            anchor="mm"
        )
        if ongoing is True:
            x = int(margin_h_left + name_width + 12 * week_width + total_width)
            draw.text(
                (x + projected_width / 2, y),
                str(data_dict[member]['projected_points']),
                font=font,
                fill=(192, 64, 0, 255),
                anchor="mm"
            )
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

    font = ImageFont.truetype(env.BOT_DIRECTORY + env.MEDIA_SUBDIRECTORY + constants.IMAGE_FONT_FILENAME, 18)

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

    image_height = int(
        margin_v_top + title_line_count * font.size * 1.5 + row_height * (len(data_dict) + 1) + margin_v_bottom
    )

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

    draw.line(
        [
            (margin_h_left, margin_v_top + title_line_count * font.size * 1.5 + row_height),
            (margin_h_left + table_width, margin_v_top + title_line_count * font.size * 1.5 + row_height)
        ],
        fill=(255, 255, 255, 255),
        width=1,
        joint=None
    )

    # Draw the members details
    members_drawn = 0

    for member in data_dict:
        x = int(margin_h_left)
        y = int(
            margin_v_top
            + title_line_count * font.size * 1.5
            + row_height
            + row_height * members_drawn
            + row_height / 2
        )
        if members_drawn % 2 == 1:
            draw.rectangle(
                [
                    (margin_h_left, int(y - row_height / 2)),
                    (margin_h_left + table_width, int(y + row_height / 2))
                ],
                fill=(24, 24, 24, 255)
            )
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


def draw_head2head_bar(
    im,
    draw,
    font,
    label,
    v_pos,
    height,
    max_scale_pixels,
    max_scale_value,
    racer1_value,
    racer2_value,
    racer1_colour,
    racer2_colour
):
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
    draw.text(
        (left - font.size / 2, bottom - bar_height / 2),
        str(racer1_value),
        font=font,
        fill=(255, 255, 255, 255),
        anchor="rm"
    )

    # Racer2
    if abs(racer2_value) > 0:
        right = im.width / 2 + max_scale_pixels * (racer2_value / max_scale_value)
    else:
        right = im.width / 2 + font.size / 4
    left = im.width / 2

    draw.rectangle([(left, bottom - bar_height), (right, bottom)], fill=racer2_colour)
    draw.text(
        (right + font.size / 2, bottom - bar_height / 2),
        str(racer2_value),
        font=font,
        fill=(255, 255, 255, 255),
        anchor="lm"
    )


def draw_head2head_bar_inverted(
    im,
    draw,
    font,
    label,
    v_pos,
    height,
    max_scale_pixels,
    max_scale_value,
    racer1_value,
    racer2_value,
    racer1_colour,
    racer2_colour
):
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
    draw.text(
        (left - font.size / 2, bottom - bar_height / 2), str(racer1_value),
        font=font,
        fill=(255, 255, 255, 255),
        anchor="rm"
    )

    # Racer2
    if abs(racer2_value) > 0:
        right = im.width / 2 + max_scale_pixels * abs(abs(racer2_value) - abs(max_scale_value)) / max_scale_value
    else:
        right = im.width / 2 + font.size / 4
    left = im.width / 2

    draw.rectangle([(left, bottom - bar_height), (right, bottom)], fill=racer2_colour)
    draw.text(
        (right + font.size / 2, bottom - bar_height / 2),
        str(racer2_value),
        font=font,
        fill=(255, 255, 255, 255),
        anchor="lm"
    )


def generate_ir_graph(member_dicts, title, print_legend, draw_license_split_line=False):
    if len(member_dicts) == 1 and 'ir_data2' in member_dicts[0]:
        draw_ir_split = True
    else:
        draw_ir_split = False

    image_width = 1000
    image_height = 320
    im = Image.new('RGBA', (image_width, image_height), color=(0, 0, 0, 0))
    bg = Image.new('RGBA', (image_width, image_height), color=(0, 0, 0, 255))
    draw = ImageDraw.Draw(im)
    font = ImageFont.truetype(
        env.BOT_DIRECTORY + env.MEDIA_SUBDIRECTORY + constants.IMAGE_FONT_FILENAME,
        int(image_height * 16 / 300)
    )
    fontsm = ImageFont.truetype(
        env.BOT_DIRECTORY + env.MEDIA_SUBDIRECTORY + constants.IMAGE_FONT_FILENAME,
        int(image_height * 12 / 300)
    )

    margin_v_top = 0.15 * image_height
    margin_v_bottom = 0.1 * image_height

    if draw_ir_split:
        margin_h_right = 0.20 * image_width
    elif print_legend:
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
            point = (point[0].timestamp() * 1000, point[1])  # Convert datetime to timestamp
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

    sports_formula_split_datetime = datetime.fromisoformat(constants.IRACING_SPORTS_FORMULA_SPLIT_DATETIME)
    sports_formula_split_timestamp = sports_formula_split_datetime.timestamp() * 1000

    max_timestamp = int(datetime.now().timestamp() * 1000)

    timestamp_range = max_timestamp - min_timestamp
    timestamp_range_pixels = image_width - margin_h_right - margin_h_left

    earliest_datetime = date.fromtimestamp(min_timestamp / 1000)
    latest_datetime = date.fromtimestamp(max_timestamp / 1000)

    earliest_year = earliest_datetime.year
    latest_year = latest_datetime.year

    dates = []

    for i in range(earliest_year + 1, latest_year + 2):
        dates.append(datetime(i, 1, 1))

    for day in dates:
        year_timestamp = int(day.timestamp()) * 1000
        x_left = margin_h_left + (((day - timedelta(days=365)).timestamp() * 1000 - min_timestamp)
                                  / timestamp_range
                                  * timestamp_range_pixels)
        if x_left < margin_h_left:
            x_left = margin_h_left
        x = margin_h_left + (year_timestamp - min_timestamp) / timestamp_range * timestamp_range_pixels
        skip_tick = False
        if x > image_width - margin_h_right:
            x = image_width - margin_h_right
            skip_tick = True
        y = image_height - margin_v_bottom
        if not skip_tick:
            draw.line([(x, y + tick_length / 2), (x, y)], fill=(255, 255, 255, 255), width=1, joint=None)
        text_width = draw.textlength(str(day.year), font=font)
        if (x - x_left) > text_width * 1.5:
            draw.text(
                (int((x + x_left) / 2), y + tick_length / 2),
                str(day.year - 1),
                font=font,
                fill=(255, 255, 255, 255),
                anchor="mt"
            )

    # Draw the licence split line
    if(draw_license_split_line):
        x = margin_h_left + (sports_formula_split_timestamp - min_timestamp) / timestamp_range * timestamp_range_pixels
        y = image_height - margin_v_bottom
        draw.line([(x, y), (x, margin_v_top)], fill=(128, 128, 128, 255), width=1, joint=None)
        draw.text(
            (x - tick_length / 2, y - int(fontsm.size * 1.5)),
            'Licence Split',
            font=fontsm,
            fill=(128, 128, 128, 255),
            anchor="ra"
        )

    for i in range(1, ir_scale_maj_divisions + 1):
        x = margin_h_left
        y = image_height - margin_v_bottom - i * ir_scale_pixels / ir_scale_maj_divisions
        if int(i * ir_scale_maj_division_size) != constants.PLEB_LINE:
            draw.line([(x, y), (image_width - margin_h_right, y)], fill=(255, 255, 255, 64), width=1, joint=None)
            draw.text(
                (x - tick_length / 2, y),
                str(i * ir_scale_maj_division_size),
                font=font,
                fill=(255, 255, 255, 255),
                anchor="rm"
            )
        else:
            draw.line([(x, y), (image_width - margin_h_right, y)], fill=(255, 0, 0, 128), width=1, joint=None)
            draw.text((x - tick_length / 2, y), str("Pleb\nLine"), font=font, fill=(255, 255, 255, 255), anchor="rm")
            pleb_line_drawn = True
    if not pleb_line_drawn:
        x = margin_h_left
        y = (
            image_height
            - margin_v_bottom
            - constants.PLEB_LINE / (ir_scale_maj_divisions * ir_scale_maj_division_size) * ir_scale_pixels
        )
        draw.line([(x, y), (image_width - margin_h_right, y)], fill=(255, 0, 0, 128), width=1, joint=None)
        draw.text((x - tick_length / 2, y), str("Pleb Line"), font=fontsm, fill=(255, 0, 0, 128), anchor="rm")

    scaled_tuples = []
    scaled_tuples_sports = []
    scaled_tuples_formula = []

    member_count = 0

    legend_v_spacing = ir_scale_pixels / 10
    box_size = legend_v_spacing * 0.75

    for member_dict in member_dicts:
        scaled_tuples.append([])
        scaled_tuples_sports.append([])
        scaled_tuples_formula.append([])
        if (
            'graph_colour' in member_dict
            and member_dict['graph_colour'] is not None
            and len(member_dict['graph_colour']) >= 4
        ):
            colour = (
                member_dict['graph_colour'][0],
                member_dict['graph_colour'][1],
                member_dict['graph_colour'][2],
                member_dict['graph_colour'][3]
            )
        else:
            colour = (
                random.randint(0, 255),
                random.randint(0, 255),
                random.randint(0, 255),
                255
            )

        if len(member_dict['name']) < 16:
            legend_name = member_dict['name']
        else:
            legend_name = member_dict['name'][0:11] + "..."

        legend_ir_text = " (" + str(member_dict['ir_data'][-1][1]) + ")"

        for i in range(0, 22 - len(legend_name) - len(legend_ir_text)):
            legend_name += " "

        legend_name += legend_ir_text
        crossed_split_in_sports_car = False
        crossed_split_in_formula_car = False

        prev_point = None
        for point in member_dict['ir_data']:
            point_timestamp = point[0].timestamp() * 1000
            scaled_tuple_x = (
                margin_h_left
                + (point_timestamp - min_timestamp) / timestamp_range * timestamp_range_pixels
            )
            scaled_tuple_y = (
                image_height
                - margin_v_bottom
                - point[1] / (ir_scale_maj_divisions * ir_scale_maj_division_size) * ir_scale_pixels
            )
            if draw_ir_split:
                if point_timestamp <= sports_formula_split_timestamp:
                    scaled_tuples[member_count].append(
                        (scaled_tuple_x, scaled_tuple_y)
                    )
                else:
                    if not crossed_split_in_sports_car and len(scaled_tuples[member_count]) > 0:
                        # Make a new interpolated point at the license crossover timestamp
                        scaled_split_x = (
                            margin_h_left
                            + ((sports_formula_split_timestamp - min_timestamp)
                                / timestamp_range
                                * timestamp_range_pixels)
                        )
                        scaled_split_y = prev_point[1] + ((scaled_split_x - prev_point[0])
                                                          / (scaled_tuple_x - prev_point[0])
                                                          * (scaled_tuple_y - prev_point[1]))
                        scaled_tuples[member_count].append((scaled_split_x, scaled_split_y))
                        scaled_tuples_sports[member_count].append((scaled_split_x, scaled_split_y))
                        crossed_split_in_sports_car = True
                    scaled_tuples_sports[member_count].append(
                        (scaled_tuple_x, scaled_tuple_y)
                    )
            else:
                scaled_tuples[member_count].append(
                    (scaled_tuple_x, scaled_tuple_y)
                )
            prev_point = (scaled_tuple_x, scaled_tuple_y)

        if draw_ir_split:
            prev_point = None
            for point in member_dict['ir_data2']:
                point_timestamp = point[0].timestamp() * 1000
                scaled_tuple_x = (
                    margin_h_left
                    + (point_timestamp - min_timestamp) / timestamp_range * timestamp_range_pixels
                )
                scaled_tuple_y = (
                    image_height
                    - margin_v_bottom
                    - point[1] / (ir_scale_maj_divisions * ir_scale_maj_division_size) * ir_scale_pixels
                )
                if point_timestamp > sports_formula_split_timestamp:
                    if not crossed_split_in_formula_car and len(scaled_tuples[member_count]) > 0:
                        # Make a new interpolated point at the license crossover timestamp
                        scaled_split_x = margin_h_left + ((sports_formula_split_timestamp - min_timestamp)
                                                          / timestamp_range
                                                          * timestamp_range_pixels)
                        scaled_split_y = prev_point[1] + ((scaled_split_x - prev_point[0])
                                                          / (scaled_tuple_x - prev_point[0])
                                                          * (scaled_tuple_y - prev_point[1]))
                        scaled_tuples_formula[member_count].append((scaled_split_x, scaled_split_y))
                        crossed_split_in_formula_car = True
                    scaled_tuples_formula[member_count].append(
                        (scaled_tuple_x, scaled_tuple_y)
                    )
                prev_point = (scaled_tuple_x, scaled_tuple_y)

        sports_car_colour = (int(colour[0] + 48), int(colour[1] + 48), int(colour[2] - 48), colour[3])
        formula_car_colour = (int(colour[0] - 48), int(colour[1] + 48), int(colour[2] + 48), colour[3])
        draw.line(
            scaled_tuples[member_count],
            fill=colour,
            width=2,
            joint="curve"
        )
        draw.line(
            scaled_tuples_sports[member_count],
            fill=sports_car_colour,
            width=2,
            joint="curve"
        )
        draw.line(
            scaled_tuples_formula[member_count],
            fill=formula_car_colour,
            width=2,
            joint="curve"
        )

        x = image_width - margin_h_right + tick_length
        y = margin_v_top + legend_v_spacing * 0.5 - box_size / 2 + member_count * legend_v_spacing

        if draw_ir_split:
            draw.rectangle(
                [(x, y), (x + box_size, y + box_size)],
                fill=sports_car_colour,
                outline=(255, 255, 255, 255),
                width=1
            )
            draw.text(
                (x + box_size * 1.5, y + box_size / 2),
                "Sports Car",
                font=font,
                fill=(255, 255, 255, 255),
                anchor="lm"
            )

            x = image_width - margin_h_right + tick_length
            y = margin_v_top + legend_v_spacing * 0.5 - box_size / 2 + (member_count + 1) * legend_v_spacing
            draw.rectangle(
                [(x, y), (x + box_size, y + box_size)],
                fill=formula_car_colour,
                outline=(255, 255, 255, 255),
                width=1
            )
            draw.text(
                (x + box_size * 1.5, y + box_size / 2),
                "Formula Car",
                font=font,
                fill=(255, 255, 255, 255),
                anchor="lm"
            )
        elif print_legend:
            draw.rectangle([(x, y), (x + box_size, y + box_size)], fill=colour, outline=(255, 255, 255, 255), width=1)
            draw.text(
                (x + box_size * 1.5, y + box_size / 2),
                legend_name,
                font=font,
                fill=(255, 255, 255, 255),
                anchor="lm"
            )

        member_count += 1

    # Draw the axes
    draw.line(
        [
            (margin_h_left, image_height - margin_v_bottom),
            (image_width - margin_h_right, image_height - margin_v_bottom)
        ],
        fill=(255, 255, 255, 255),
        width=2,
        joint=None
    )
    draw.line(
        [
            (margin_h_left, image_height - margin_v_bottom),
            (margin_h_left, margin_v_top)
        ],
        fill=(255, 255, 255, 255),
        width=2,
        joint=None
    )

    im = Image.alpha_composite(bg, im)
    return im


def generate_cpi_graph(member_dict, title, print_legend):
    image_width = 1000
    image_height = 420
    im = Image.new('RGBA', (image_width, image_height), color=(0, 0, 0, 0))
    bg = Image.new('RGBA', (image_width, image_height), color=(0, 0, 0, 255))
    draw = ImageDraw.Draw(im)
    font = ImageFont.truetype(env.BOT_DIRECTORY + env.MEDIA_SUBDIRECTORY + constants.IMAGE_FONT_FILENAME, int(18))
    fontsm = ImageFont.truetype(env.BOT_DIRECTORY + env.MEDIA_SUBDIRECTORY + constants.IMAGE_FONT_FILENAME, int(12))

    margin_v_top = 0.2 * image_height
    margin_v_bottom = 0.2 * image_height

    if print_legend:
        margin_h_right = 0.27 * image_width
    else:
        margin_h_right = 0.15 * image_height

    margin_h_left = 0.1 * image_width

    tick_length = 0.05 * image_height

    # Draw the title
    title_lines = title.split("\n")
    if len(title_lines) > 0:
        draw.text(
            (image_width * 0.5, margin_v_top * 0.33),
            title_lines[0],
            font=font,
            fill=(255, 255, 255, 255),
            anchor="mm"
        )
    if len(title_lines) > 1:
        draw.text(
            (image_width * 0.5, margin_v_top * 0.66),
            title_lines[1],
            font=font,
            fill=(255, 255, 255, 255),
            anchor="mm"
        )

    # Draw the x-axis label
    draw.text(
        (
            margin_h_left + (image_width - margin_h_left - margin_h_right) / 2,
            image_height - margin_v_bottom + tick_length + font.size * 2
        ),
        "Total Corners",
        font=font,
        fill=(255, 255, 255, 255),
        anchor="mm"
    )

    max_cpi = 0
    max_corners = 0
    min_timestamp = 10000000000000

    date_points = []

    prev_point = None
    for point in member_dict['cpi_data']:
        if prev_point is not None:
            if(point[0].year > prev_point[0].year):
                # The two cpi points span a year. Generate a year boundary data point
                # interpolated between the two lap counts.
                prev_total_corners = prev_point[1]
                prev_date = prev_point[0]
                total_corners = point[1]
                point_date = point[0]

                timespan = point_date - prev_date
                cornerspan = total_corners - prev_total_corners

                new_year = datetime(point_date.year, 1, 1, tzinfo=timezone.utc)

                time_to_point = new_year - prev_date

                corners_at_new_year = prev_total_corners + time_to_point / timespan * cornerspan

                date_points.append((new_year, corners_at_new_year))
        prev_point = point
        point = (point[0].timestamp() * 1000, point[1], point[2])  # Convert the datetime to a timestamp
        if point[2] > max_cpi:
            max_cpi = point[2]
        if point[0] < min_timestamp:
            min_timestamp = point[0]
        if point[1] > max_corners:
            max_corners = point[1]

    cpi_scale_maj_divisions = 5
    cpi_scale_maj_division_size = round_up_to_nearest_125(max_cpi / cpi_scale_maj_divisions)
    cpi_scale_pixels = (image_height - margin_v_bottom - margin_v_top)

    max_timestamp = int(datetime.now().timestamp() * 1000)

    # timestamp_range = max_timestamp - min_timestamp
    # timestamp_range_pixels = image_width - margin_h_right - margin_h_left

    total_corners_scale_maj_divisions = 8
    total_corners_scale_maj_division_size = round_up_to_nearest_125(max_corners / total_corners_scale_maj_divisions)
    total_corners_scale_pixels = image_width - margin_h_right - margin_h_left
    total_corners_scale_maj_divisions = math.ceil(max_corners / total_corners_scale_maj_division_size)

    earliest_datetime = date.fromtimestamp(min_timestamp / 1000)
    latest_datetime = date.fromtimestamp(max_timestamp / 1000)

    earliest_year = earliest_datetime.year
    latest_year = latest_datetime.year

    dates = []

    for i in range(earliest_year + 1, latest_year + 1):
        dates.append(datetime(i, 1, 1))

    for i in range(1, total_corners_scale_maj_divisions + 1):
        x = margin_h_left + i * total_corners_scale_pixels / total_corners_scale_maj_divisions
        y = image_height - margin_v_bottom
        draw.line([(x, y + tick_length / 2), (x, y)], fill=(255, 255, 255, 255), width=1, joint=None)
        draw.text(
            (x, y + tick_length),
            f"{int(i * total_corners_scale_maj_division_size):,}",
            font=font,
            fill=(255, 255, 255, 255),
            anchor="mt"
        )

    prev_scaled_x = margin_h_left
    for date_point in date_points:
        scaled_x = (
            margin_h_left
            + (date_point[1] / (total_corners_scale_maj_divisions * total_corners_scale_maj_division_size) * total_corners_scale_pixels)
        )
        text_x = (scaled_x + prev_scaled_x) / 2
        prev_scaled_x = scaled_x
        draw.line(
            [(scaled_x, margin_v_top), (scaled_x, image_height - margin_v_bottom)],
            fill=(255, 255, 255, 64),
            width=1, joint=None
        )
        draw.text(
            (text_x, margin_v_top + fontsm.size / 2),
            f"{date_point[0].year - 1}",
            font=fontsm,
            fill=(255, 255, 255, 64),
            anchor="mt"
        )

    # Add the year label past the final division line
    if(len(date_points) > 0):
        text_x = (image_width - margin_h_right + prev_scaled_x) / 2
        draw.text(
            (text_x, margin_v_top + fontsm.size / 2),
            f"{date_point[0].year}",
            font=fontsm,
            fill=(255, 255, 255, 64),
            anchor="mt"
        )

    # for day in dates:
    #     year_timestamp = int(day.timestamp()) * 1000
    #     x = margin_h_left + (year_timestamp - min_timestamp) / timestamp_range * timestamp_range_pixels
    #     y = image_height - margin_v_bottom
    #     draw.line([(x, y + tick_length / 2), (x, y)], fill=(255, 255, 255, 255), width=1, joint=None)
    #     if len(dates) < 6:
    #         draw.text((x, y + tick_length), str(day.year) + "-1-1", font=font, fill=(255, 255, 255, 255), anchor="mt")
    #     else:
    #         draw.text((x, y + tick_length), str(day.year), font=font, fill=(255, 255, 255, 255), anchor="mt")

    for i in range(1, cpi_scale_maj_divisions + 1):
        x = margin_h_left
        y = image_height - margin_v_bottom - i * cpi_scale_pixels / cpi_scale_maj_divisions
        draw.line([(x, y), (image_width - margin_h_right, y)], fill=(255, 255, 255, 64), width=1, joint=None)
        draw.text(
            (x - tick_length / 2, y),
            str(i * cpi_scale_maj_division_size),
            font=font,
            fill=(255, 255, 255, 255),
            anchor="rm"
        )

    scaled_tuples = []

    legend_v_spacing = cpi_scale_pixels / 10
    box_size = legend_v_spacing * 0.75

    if (
        'graph_colour' in member_dict
        and member_dict['graph_colour'] is not None
        and len(member_dict['graph_colour']) >= 4
    ):
        colour = (
            member_dict['graph_colour'][0],
            member_dict['graph_colour'][1],
            member_dict['graph_colour'][2],
            member_dict['graph_colour'][3]
        )
    else:
        colour = (
            random.randint(0, 255),
            random.randint(0, 255),
            random.randint(0, 255),
            255
        )

    for point in member_dict['cpi_data']:
        scaled_tuple_x = (
            margin_h_left
            + (point[1] / (total_corners_scale_maj_divisions * total_corners_scale_maj_division_size) * total_corners_scale_pixels)
        )
        scaled_tuple_y = (
            image_height
            - margin_v_bottom
            - point[2] / (cpi_scale_maj_divisions * cpi_scale_maj_division_size) * cpi_scale_pixels
        )
        scaled_tuples.append(
            (scaled_tuple_x, scaled_tuple_y)
        )

    draw.line(scaled_tuples, fill=colour, width=2, joint="curve")
    x = image_width - margin_h_right + tick_length
    y = margin_v_top + legend_v_spacing * 0.5 - box_size / 2

    # Draw the axes
    draw.line(
        [
            (margin_h_left, image_height - margin_v_bottom),
            (image_width - margin_h_right, image_height - margin_v_bottom)
        ],
        fill=(255, 255, 255, 255),
        width=2,
        joint=None
    )
    draw.line(
        [
            (margin_h_left, image_height - margin_v_bottom),
            (margin_h_left, margin_v_top)
        ],
        fill=(255, 255, 255, 255),
        width=2,
        joint=None
    )

    im = Image.alpha_composite(bg, im)
    return im


def round_up_to_nearest_125(value):

    if value is None:
        return None

    if value == 0:
        return 1

    tmp_value = value
    order = 0
    if tmp_value >= 1:
        tmp_value = tmp_value / 10

        while tmp_value > 1:
            tmp_value /= 10
            order += 1
        tmp_value *= 10
    else:
        tmp_value = tmp_value

        while tmp_value < 1:
            tmp_value *= 10
            order -= 1

    if tmp_value <= 2:
        tmp_value = 2
    elif tmp_value <= 5:
        tmp_value = 5
    else:
        tmp_value = 10

    rounded_value = tmp_value * math.pow(10, order)

    return rounded_value


def get_max_scale(value1, value2):
    max_value = abs(value1)
    if abs(value2) > abs(value1):
        max_value = abs(value2)

    return round_up_to_nearest_125(max_value)

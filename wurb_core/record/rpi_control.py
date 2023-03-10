#!/usr/bin/python3
# -*- coding:utf-8 -*-
# Project: http://cloudedbats.org, https://github.com/cloudedbats
# Copyright (c) 2020-present Arnold Andreasson
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).

import asyncio
import logging
import os
import datetime
import pathlib
import psutil


class WurbRaspberryPi(object):
    """ """

    def __init__(self, logger="DefaultLogger"):
        """ """
        self.logger_name = logger
        self.logger = logging.getLogger(logger)
        self.os_raspbian = None

    async def rpi_control(self, command):
        """ """
        if command == "rpi_status":
            await self.rpi_status()
            return

        # First check: OS Raspbian. Only valid for Raspbian and user pi.
        if self.is_os_raspbian():
            # Select command.
            if command == "rpi_shutdown":
                await self.rpi_shutdown()
            elif command == "rpi_reboot":
                await self.rpi_reboot()
            elif command == "rpi_sd_to_usb":
                await self.rpi_sd_to_usb()
            # elif command == "rpi_clear_sd_ok":
            elif command == "rpi_clear_sd":
                await self.rpi_clear_sd()
            else:
                # Logging.
                message = "Raspberry Pi command failed. Not a valid command: " + command
                wurb_core.wurb_logger.error(message)
        else:
            # Logging.
            message = "Raspberry Pi command failed (" + command + "), not Raspbian OS."
            wurb_core.wurb_logger.warning(message)

    async def set_detector_time(self, posix_time_s, cmd_source=""):
        """ Only valid for Raspbian and user pi. """
        try:
            local_datetime = datetime.datetime.fromtimestamp(posix_time_s)
            # utc_datetime = datetime.datetime.utcfromtimestamp(posix_time_s)
            # local_datetime = utc_datetime.replace(
            #     tzinfo=datetime.timezone.utc
            # ).astimezone(tz=None)
            time_string = local_datetime.strftime("%Y-%m-%d %H:%M:%S")
            print(time_string)
            # Logging.
            message = "Detector time update: " + time_string
            if cmd_source:
                message += " (" + cmd_source + ")."
            wurb_core.wurb_logger.info(message)
            # First check: OS Raspbian.
            if self.is_os_raspbian():
                # Second check: User pi exists. Perform: "date --set".
                os.system('cd /home/pi && sudo date --set "' + time_string + '"')
            else:
                # Logging.
                message = "Detector time update failed, not Raspbian OS."
                wurb_core.wurb_logger.warning(message)
        except Exception as e:
            # Logging error.
            message = "RPi set_detector_time: " + str(e)
            wurb_core.wurb_logger.error(message)

    def get_settings_dir_path(self):
        """ """
        rpi_dir_path = "/home/pi/"  # For RPi SD card with user 'pi'.
        # Default for not Raspberry Pi.
        dir_path = pathlib.Path("wurb_settings")
        if pathlib.Path(rpi_dir_path).exists():
            dir_path = pathlib.Path(rpi_dir_path, "wurb_settings")
        # Create directories.
        if not dir_path.exists():
            dir_path.mkdir(parents=True)
        return dir_path

    def get_wavefile_target_dir_path(self):
        """ """
        file_directory = wurb_core.wurb_settings.get_setting("fileDirectory")
        # Add date to file directory.
        date_option = wurb_core.wurb_settings.get_setting("fileDirectoryDateOption")
        used_date_str = ""
        if date_option in ["date-pre-true", "date-post-true"]:
            used_date = datetime.datetime.now()
            used_date_str = used_date.strftime("%Y-%m-%d")
        if date_option in ["date-pre-after", "date-post-after"]:
            used_date = datetime.datetime.now() + datetime.timedelta(hours=12)
            used_date_str = used_date.strftime("%Y-%m-%d")
        if date_option in ["date-pre-before", "date-post-before"]:
            used_date = datetime.datetime.now() - datetime.timedelta(hours=12)
            used_date_str = used_date.strftime("%Y-%m-%d")
        if date_option in ["date-pre-true", "date-pre-after", "date-pre-before"]:
            file_directory = used_date_str + "_" + file_directory
        if date_option in ["date-post-true", "date-post-after", "date-post-before"]:
            file_directory = file_directory + "_" + used_date_str
        # Defaults for RPi.
        target_rpi_media_path = "/media/pi/"  # For RPi USB.
        target_rpi_internal_path = "/home/pi/"  # For RPi SD card with user 'pi'.
        dir_path = None

        # Example code:
        # hdd = psutil.disk_usage(str(dir_path))
        # total_disk = hdd.total / (2**20)
        # used_disk = hdd.used / (2**20)
        # free_disk = hdd.free / (2**20)
        # percent_disk = hdd.percent
        # print("Total disk: ", total_disk, "MB")
        # print("Used disk: ", used_disk, "MB")
        # print("Free disk: ", free_disk, "MB")
        # print("Percent: ", percent_disk, "%")

        # Check mounted USB memory sticks. At least 20 MB left.
        rpi_media_path = pathlib.Path(target_rpi_media_path)
        if rpi_media_path.exists():
            for usb_stick_name in sorted(list(rpi_media_path.iterdir())):
                usb_stick_path = pathlib.Path(rpi_media_path, usb_stick_name)
                # Directory may exist even when no USB attached.
                if usb_stick_path.is_mount():
                    hdd = psutil.disk_usage(str(usb_stick_path))
                    free_disk = hdd.free / (2 ** 20)  # To MB.
                    if free_disk >= 20.0:  # 20 MB.
                        return pathlib.Path(usb_stick_path, file_directory)

        # Check internal SD card. At least 500 MB left.
        rpi_internal_path = pathlib.Path(target_rpi_internal_path)
        if rpi_internal_path.exists():
            hdd = psutil.disk_usage(str(rpi_internal_path))
            free_disk = hdd.free / (2 ** 20)  # To MB.
            if free_disk >= 500.0:  # 500 MB.
                return pathlib.Path(rpi_internal_path, "wurb_recordings", file_directory)
            else:
                # Logging error.
                message = "RPi Not enough space left on RPi SD card."
                wurb_core.wurb_logger.error(message)
                return None  # Not enough space left on RPi SD card.

        # Default for not Raspberry Pi.
        dir_path = pathlib.Path("wurb_recordings", file_directory)
        return dir_path

    def is_os_raspbian(self):
        """ Check OS version for Raspberry Pi. """
        if self.os_raspbian is not None:
            return self.os_raspbian
        else:
            try:
                os_version_path = pathlib.Path("/etc/os-release")
                if os_version_path.exists():
                    with os_version_path.open("r") as os_file:
                        os_file_content = os_file.read()
                        # print("Content of /etc/os-release: ", os_file_content)
                        if "raspbian" in os_file_content:
                            self.os_raspbian = True
                        else:
                            self.os_raspbian = False
                else:
                    self.os_raspbian = False
            except Exception as e:
                # Logging error.
                message = "RPi is_os_raspbian: " + str(e)
                wurb_core.wurb_logger.error(message)
        #
        return self.os_raspbian

    async def rpi_shutdown(self):
        """ """
        # Logging.
        message = "The Raspberry Pi command 'Shutdown' is activated."
        wurb_core.wurb_logger.info(message)
        await asyncio.sleep(1.0)
        #
        os.system("cd /home/pi && sudo shutdown -h now")

    async def rpi_reboot(self):
        """ """
        # Logging.
        message = "The Raspberry Pi command 'Reboot' is activated."
        wurb_core.wurb_logger.info(message)
        await asyncio.sleep(1.0)
        #
        os.system("cd /home/pi && sudo reboot")

    async def rpi_sd_to_usb(self):
        """ """
        # Logging.
        message = "The Raspberry Pi command 'Copy SD to USB' is not implemented."
        wurb_core.wurb_logger.info(message)

    async def rpi_clear_sd(self):
        """ """
        # Logging.
        message = "The Raspberry Pi command 'Clear SD card' is not implemented."
        wurb_core.wurb_logger.info(message)

    async def rpi_status(self):
        """ """
        # Mic.
        rec_status = await wurb_core.wurb_recorder.get_rec_status()
        if rec_status != "Microphone is on.":
            await wurb_core.ultrasound_devices.check_devices()
            device_name = wurb_core.ultrasound_devices.device_name
            sampling_freq_hz = wurb_core.ultrasound_devices.sampling_freq_hz
            if device_name:
                # Logging.
                message = "Connected microphone: "
                message += device_name
                message += " Frequency: "
                message += str(sampling_freq_hz)
                message += " Hz."
                wurb_core.wurb_logger.info(message)
            else:
                # Logging.
                message = "No microphone is found. "
                wurb_core.wurb_logger.info(message)

        # Solartime.
        solartime_dict = await wurb_core.wurb_scheduler.get_solartime_data(
            print_new=False
        )
        if solartime_dict:
            sunset_utc = solartime_dict.get("sunset", None)
            dusk_utc = solartime_dict.get("dusk", None)
            dawn_utc = solartime_dict.get("dawn", None)
            sunrise_utc = solartime_dict.get("sunrise", None)
            if sunset_utc and dusk_utc and dawn_utc and sunrise_utc:
                sunset_local = sunset_utc.astimezone()
                dusk_local = dusk_utc.astimezone()
                dawn_local = dawn_utc.astimezone()
                sunrise_local = sunrise_utc.astimezone()
                message = "Solartime: "
                message += " Sunset: " + sunset_local.strftime("%H:%M:%S")
                message += " Dusk: " + dusk_local.strftime("%H:%M:%S")
                message += " Dawn: " + dawn_local.strftime("%H:%M:%S")
                message += " Sunrise: " + sunrise_local.strftime("%H:%M:%S")
                wurb_core.wurb_logger.info(message)
        else:
            # Logging. 
            message = "Can't calculate solartime. Lat/long is missing."
            wurb_core.wurb_logger.info(message)

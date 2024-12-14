# Copyright © 2023 Takenoko
# MIT 라이선스로 배포
# https://opensource.org/licenses/mit-license.php

import glob
import os
import piexif
import piexif.helper
from PIL import Image, PngImagePlugin
from datetime import datetime
from pywintypes import Time

# Windows 환경인지 확인
on_windows = os.name == 'nt'
if on_windows:
    import win32file
    import win32con

# WEBP 압축 품질 (무손실 압축을 위해 100으로 설정)
WEBP_QUALITY = 100  # 무손실 압축을 위해 100으로 변경
# 이미지 형식
IMG_INPUT_FORMAT = 'PNG'
IMG_OUTPUT_FORMAT = 'WEBP'
# 이미지 확장자
IMG_INPUT_FILENAME_EXT = 'png'
IMG_OUTPUT_FILENAME_EXT = 'webp'
# 디렉토리
INPUT_DIR = 'inputs/'
OUTPUT_DIR = 'outputs/'

# 변환할 PNG 파일 목록 가져오기
files = glob.glob(INPUT_DIR + '*.' + IMG_INPUT_FILENAME_EXT)

# 각 PNG 파일을 WEBP로 변환하고 저장
for file in files:
    file_name = os.path.splitext(os.path.basename(file))[0]
    output_file_name = file_name + '.' + IMG_OUTPUT_FILENAME_EXT
    output_file_path = OUTPUT_DIR + output_file_name
    output_file_abspath = os.path.abspath(OUTPUT_DIR + output_file_name)

    def get_png_info(file):
        try:
            # 이미지 열기
            img = Image.open(file)
            # PNG 정보 가져오기
            png_info = img.info
            # 이미지 닫기
            img.close()
            return png_info
        except Exception as e:
            print(f"이미지를 열 수 없습니다: {e}")
            return None

    # PNG 파일에서 정보 가져오기
    png_info = get_png_info(file)

    # 이미지 열기
    image = Image.open(file)

    # 파일 시간 정보 가져오기
    access_time = os.path.getatime(file)  # 접근 시간
    modify_time = os.path.getmtime(file)  # 수정 시간

    if on_windows:
        creation_time = os.path.getctime(file)  # 생성 시간

    # WEBP로 변환 (무손실 압축)
    image.save(output_file_path, IMG_OUTPUT_FORMAT, quality=WEBP_QUALITY)

    # 이미지 닫기
    image.close()

    # WEBP 파일에 Exif 데이터 (PNG 정보) 저장
    if png_info is not None:
        # PNG 정보를 문자열로 변환
        png_info_data = ""
        for key, value in png_info.items():
            if key == 'parameters':
                # Automatic1111 형식
                png_info_data += f"{value}\n"
            else:
                # NovelAI 형식
                png_info_data += f"{key}: {value}\n"

        png_info_data = png_info_data.rstrip()

        # Exif 데이터 생성
        exif_dict = {"Exif": {piexif.ExifIFD.UserComment: piexif.helper.UserComment.dump(png_info_data or '', encoding='unicode')}}

        # Exif 데이터를 바이트로 변환
        exif_bytes = piexif.dump(exif_dict)

        # Exif 데이터를 삽입하여 WEBP 파일 저장
        piexif.insert(exif_bytes, output_file_path)

    else:
        print("PNG 정보를 가져올 수 없습니다.")

    # 파일 시간 정보 설정 (Windows)
    if on_windows:
        handle = win32file.CreateFile(
            output_file_path,
            win32con.GENERIC_WRITE,
            win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE | win32con.FILE_SHARE_DELETE,
            None,
            win32con.OPEN_EXISTING,
            0,
            None
        )
        # 파일 시간 설정
        win32file.SetFileTime(handle, Time(creation_time), Time(access_time), Time(modify_time))
        # 핸들 닫기
        handle.Close()

    # 파일 시간 정보 설정 (다른 운영체제)
    os.utime(output_file_path, (access_time, modify_time))


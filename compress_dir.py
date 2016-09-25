from PIL import Image
import qrcode
import tarfile
import subprocess
import numpy
import gnupg

MAX_DATA_PER_QR = 2700
QR_CODES_PER_FRAME = 60
YOUTUBE_VIDEO_DIMENSIONS = (1920, 1080)
FFMPEG_BIN = "ffmpeg"


def make_tarfile(output_filename, source_dir):
    with tarfile.open(output_filename, "w:gz") as tar:
        tar.add(source_dir, source_dir)
        
def encrypt_tar(output, source, public_key):
    gpg = gnupg.GPG(public_key)
    with open('storage.tar', 'rb') as f:
    status = gpg.encrypt_file(
        f, recipients=['User'],
        always_trust='true',
        output='storage.tar.gpg')
    


def qr_encode(zipped_dir):
    qr_codes = []
    qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
    bytesread = 0
    with open(zipped_dir, 'r') as f:
        for line in f:
            print bytesread
            bytesread += len(line)
            if bytesread >= MAX_DATA_PER_QR:
                bytesread -= len(line)
                qr.make(fit=True)
                img_file = qr.make_image()
                qr_codes.append(img_file)
                qr = qrcode.QRCode(
                        version=1,
                        error_correction=qrcode.constants.ERROR_CORRECT_L,
                        box_size=10,
                        border=4,
                    )
                bytesread = len(line)
            qr.add_data(line)
    if bytesread > 0:
        qr.make(fit=True)
        img_file = qr.make_image()
        qr_codes.append(img_file)
    return qr_codes


def stitch_images(image_files):
    canvas = Image.new('RGB', YOUTUBE_VIDEO_DIMENSIONS)
    image_count = 0
    frames = []
    while image_count < len(image_files):
        for i in xrange(0, 1100, 100):
            for j in xrange(0, 700, 100):
                im = image_files[i]
                im.thumbnail(100, 100)
                canvas.paste(im, (i, j))
                image_count += 1
                if image_count >= len(image_files):
                    break
        frames.append(canvas)
        canvas = Image.new('RGB', YOUTUBE_VIDEO_DIMENSIONS)
        for i, qr in enumerate(frames):
            qr.save("frame" + i + ".png")
    return frames


def convert_to_mp4(image_files, output_filename):
    command = [FFMPEG_BIN, '-y',  # (optional) overwrite output file if it exists
                '-f', 'rawvideo',
                '-vcodec', 'rawvideo',
                '-s', '177x177',  # size of one frame
                '-pix_fmt', 'rgb24',
                '-r', '24',  # frames per second
                '-i', '-',  # The imput comes from a pipe
                '-an',  # Tells FFMPEG not to expect any audio
                '-vcodec', 'mpeg',
                output_filename]
    pipe = subprocess.Popen(command, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    for image in image_files:
        pipe.stdin.write(image)
    pipe.stdin.close()
    pipe.stderr.close()

if __name__ == '__main__':
    make_tarfile('compressed_test', 'test')
    encrypt_tar('test', 'test', 'public_key')
    os.system('storage.tar')
    compressed_images = qr_encode('compressed_test')
    # frames = stitch_images(compressed_images)
    convert_to_mp4(compressed_images, 'vid_for_tube.mp4')

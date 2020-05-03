#!/usr/bin/env python

import os, os.path, sys
import zipfile, patoolib
import argparse
import tempfile
import logging, traceback

from PIL import Image
import img2pdf

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('zip2pdf')

def isZipFileName(fileName):
    fileExt = fileName[-4:].lower()
    if (fileExt == ".zip" or fileExt == ".cbz" or 
        fileExt == ".rar" or fileExt == ".cbr"):
        
        #logger.info(f"isZipFileName({fileName}): True")
        return True

    #logger.info(f"isZipFileName({fileName}): False")
    return False


def unzipFile(fileName, destinationDir = None):
    result = False
    if not isZipFileName(fileName):
        logger.error(f"unzipFile({fileName}) not zip file")
        return False

    if destinationDir == None:
        destinationDir = fileName[-4:]

    try:
        if fileName[-1].lower() == 'r': # rar type
            patoolib.util.log_info = logger.info
            patoolib.extract_archive(fileName, outdir=destinationDir)
            logger.info(f"unrared: {fileName}")
        else: # zipfile
            zip = zipfile.ZipFile(fileName, 'r')
            zip.extractall(destinationDir)
            zip.close()
            logger.info(f"unzipped: {fileName}")

        result = True

    except:
        result = False
        logger.error(f"unzipping {fileName} failed")
        traceback.print_exc()

    #for root, dirs, files in os.walk(destinationDir):
        #for name in files:
            #logger.info(os.path.join(root, name))

    return result


def getZipFileList(rootDir):
    localFileList = []
    logger.info(f"getZipFileList({rootDir})")

    if os.path.isdir(rootDir):
        tempFileNames = os.listdir(rootDir)
        for tempFileName in tempFileNames:
            joinedName = os.path.join(rootDir, tempFileName)

            if os.path.isdir(joinedName):
                localFileList.extend(getZipFileList(joinedName))

            if isZipFileName(joinedName):
                localFileList.append(joinedName)
    else:
        if isImageFileName(rootDir):
            localFileList.append(rootDir)
    
    #logger.info(f"getZipFileList({rootDir}) {len(localFileList)}")
    #for i, fileName in enumerate(localFileList):
        #logger.info(f"{i}: {fileName}")

    return localFileList


def isImage(fileName):
    result = False
    try:
        with Image.open(fileName) as img:
            width = img.width
            height = img.height

            if width > 10 and height > 10:
                #logger.info("isImage({fileName}) height:{height} width:{width} True")
                result = True
            else:
                #logger.info("isImage({fileName}) height:{height} width:{width} False")
                pass

            if result == True:
                img.load()
                if img.mode == "RGBA":
                    background = Image.new("RGB", img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[3]) # 3 is the alpha channel
                    background.save(fileName, "JPEG", quality=80)
                    #newImg = img.quantize(colors=256, method=2)
                    #newImg.save(fileName)
                elif img.mode == "P":
                    newImg = img.convert('RGB')
                    newImg.save(fileName)

    except:
        #logger.info("isImage({fileName}) False")
        traceback.print_exc()
    return result


def isImageFileName(fileName):
    fileExt = fileName[-4:].lower()

    if (fileExt == ".jpg" or fileExt == "jpeg" or 
        fileExt == ".gif" or
        fileExt == ".bmp" or
        fileExt == ".png"):
        #logger.info(f"isImageFileName({fileName}): True")
        return isImage(fileName)

    #logger.info(f"isImageFileName({fileName}): False")
    return False

def removeAlpha(fileName):
    try:
        img = Image.open(fileName)
        #newImg = img.quantize(colors=256, method=2)
        newImg = img.convert("RGB")
        newImg.save(fileName)
    except:
        logger.error(f"removeAlpha({fileName}) failed")
        traceback.print_exc()

def getImageFileList(rootDir):
    localFileList = []
    logger.info(f"getImageFileList({rootDir})")

    if os.path.isdir(rootDir):
        tempFileNames = os.listdir(rootDir)
        for tempFileName in tempFileNames:
            if tempFileName.startswith('.'):
                continue

            joinedName = os.path.join(rootDir, tempFileName)

            if os.path.isdir(joinedName):
                localFileList.extend(getImageFileList(joinedName))

            if isImageFileName(joinedName):
                localFileList.append(joinedName)
    else:
        if isImageFileName(rootDir):
            localFileList.append(rootDir)
    
    if len(localFileList) > 0:
        with Image.open(localFileList[0]) as img:
            logger.info(f"name:{localFileList[0]} mode:{img.mode} ")
    #logger.info(f"getImageFileList({rootDir}) {len(localFileList)}")
    #for i, fileName in enumerate(localFileList):
        #logger.info(f"{i}: {fileName}")

    localFileList.sort(key=lambda item: (-len(item), item))

    return localFileList


def saveImageListToPdf(imageList, outputFileName):
    # pillow option
    if imageList == None or len(imageList) == 0:
        return
    logger.info(f"saveImageListToPdf outputFileName:{outputFileName}")
    try:
        firstPage = imageList[0]
        if len(imageList) > 1:
            restImages = imageList[1:]
            firstPage.save(outputFileName, format="PDF" ,resolution=100.0, save_all=True, append_images=restImages)
        else:
            firstPage.save(outputFileName, format="PDF", resolution=100.0)

        for im in imageList:
            im.close()
        logger.error("saveImageListToPdf saved a PDF file")
    except:
        logger.error("saveImageListToPdf error")
        traceback.print_exc()


def toPdf(fileName):
    if len(fileName) <= 0: 
        return

    outputFileName = fileName[:-4] + ".pdf"
    logger.info(f"toPdf({fileName}) to {outputFileName}")
    with tempfile.TemporaryDirectory() as tempDir:
        logger.info(f"start unzipping the file {fileName} to {tempDir}")
        if unzipFile(fileName, tempDir):
            logger.info(f"getting image file list")
            imageFileList = getImageFileList(tempDir)

            if len(imageFileList) >= 12:
                logger.info("trying img2pdf.convert()")
                with open(outputFileName, "wb") as outputFile:
                    outputFile.write(img2pdf.convert(imageFileList))
                logger.info(f"done with {outputFileName}")

    return outputFileName


def main(args=None):
    cwd = os.getcwd()
    zipFileList = []

    if args is not None:
        if len(args.source_files) > 0:
            zipFileList = args.source_files

    if len(zipFileList) == 0:
        zipFileList = getZipFileList(cwd)
    if len(zipFileList) == 1:
        zipFileList = getZipFileList(os.path.join(cwd, zipFileList[0]))

    if len(zipFileList) <= 0:
        return

    zipFileList2 = []
    for fileName in zipFileList:
        # remove files with PDFs
        pdfFileName = fileName[:-4] + ".pdf"
        if not os.path.exists(pdfFileName):
            zipFileList2.append(fileName)

    zipFileList2.sort()
    for fileName in zipFileList2:
        logger.info(toPdf(fileName))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Convert ZIP/CBZ files to PDFs')
    parser.add_argument('source_files', help='zip/cbz files', nargs="*")

    args = parser.parse_args()
    if args == None or len(args.source_files) <= 0:
        logger.info("No files to process")
        sys.exit(0)

    sys.exit(main(args))

# from pdfminer.high_level import  extract_pages, extract_text
#
#
# for page_layout in extract_pages("exampleFile.pdf"):
#     for element in page_layout:
#         print(element)

import fitz
import numpy
from PIL import Image
import io
from matplotlib import pyplot as plt
import cv2
import numpy as np

def pdf_to_img(path):
    pdf = fitz.open(path)
    counter = 1
    pages = []
    for i in range (len(pdf)):
        page = pdf[i]
        images = page.get_images()
        for image in images:
            base_img = pdf.extract_image(image[0])
            image_data = base_img["image"]
            img = Image.open(io.BytesIO(image_data))
            #extension = base_img["ext"]
            #img.save(open(f"image{counter}.{extension}", "wb"))
            pages.append(img)
            #counter += 1

    return pages


proba1 = pdf_to_img("proba1.pdf")



for i in range(len(proba1)):
    proba1[i] = cv2.cvtColor(np.array(proba1[i]), cv2.COLOR_BGR2RGB)


# https://stackoverflow.com/questions/28816046/
# displaying-different-images-with-actual-size-in-matplotlib-subplot
def display(im_path):
    dpi = 80
    im_data = plt.imread(im_path)

    height, width = im_data.shape[:2]

    # What size does the figure need to be in inches to fit the image?
    figsize = width / float(dpi), height / float(dpi)

    # Create a figure of the right size with one axes that takes up the full figure
    fig = plt.figure(figsize=figsize)
    ax = fig.add_axes([0, 0, 1, 1])

    # Hide spines, ticks, etc.
    ax.axis('off')

    # Display the image.
    ax.imshow(im_data, cmap='gray')

    plt.show()


display("image1.png")


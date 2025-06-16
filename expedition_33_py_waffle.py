# import libraries
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from pywaffle import Waffle
from PIL import Image

# where is image you want to merge with waffle
image_loc = r'C:\Users\nickp\OneDrive\Desktop\Home Data Projects\Viz\mtb-viz-challenge\\'
paintress_loc = 'monolith.png'

plt.rcParams["font.family"] = "Arial"
plt.rcParams['text.color'] = 'white'

# make and save waffle
plt.rcParams["font.family"] = "Arial"
plt.rcParams['text.color'] = 'white'

fig = plt.figure(
    FigureClass=Waffle,
    figsize=(8,6),
    facecolor='none',
    rows=10,
    values=[22,78],
    icons='palette',
    colors=['#ae56ee','#f3e6f8'],
    font_size=34,
    title={
        'label': '22% of Xbox Players Have Beat the Paintress (06-08-2025)',
        'loc': 'left',
        'fontdict': {
            'fontsize': 18,
            'weight':'bold'
        }
    },
    legend={
        'labels': ['Beat the Paintress', 'Yet to Beat the Paintress'], 
        'loc': 'lower left', 
        'bbox_to_anchor': (0, -0.1),
        'framealpha': 0,
        'ncol':5,
        'fontsize': 12
    }
)
paintress_waffle = 'paintress_waffle.png'
fig.savefig(image_loc+paintress_waffle)

# merge images
# Open the background image
overlay = Image.open(image_loc+paintress_waffle)
overlay_copy = overlay.copy()
# Open the image to paste
background = Image.open(image_loc+paintress_loc)
background_copy = background.copy()

background_copy.paste(overlay_copy,(20,10),mask=overlay)
background_copy
background_copy.save(image_loc+'paintress_waffle_full.png')
# RawStudio

RawStudio is my simple web photo editor. It uses flet which runs off python on a cloud server and shows a flutter UI in your browser. The image processing is done with OpenCV and NumPy. You pick a photo, make some adjustments with the sliders, and get your photo. Fr better than lightroom.

## What it does

You open an image with the Open button and it shows up in the middle. Then you can mess with the settings on the right:

- Light: Exposure, Brightness, Contrast, Highlights, Shadows
- Color: Temperature, Tint, Saturation, Shadow Tint, Highlight Tint
- Channels: Red / Green / Blue scale for fixing color casts
- Effects: Clarity, Vignette, Blur, Sharpen
- Transform: flip, grayscale, auto select (tries to pick out the main subject in the photo and dims the background)

Also rotate and reset, zoom in and out, and pan around to look at images closer. There is a histogram in the corner. You can save the result as PNG, JPG, or BMP.

## How it works

When you open a photo it decodes it and makes a smaller preview so the sliders update fast enough. Every time you move a slider it reprocesses the image on the server and sends the new picture over. When you save, it runs the full size version.

Only 2 renders can run at the same time to keep the server from getting overloaded. Uploads are capped at 60 MB and 40 megapixels.

## Running locally

```
pip install -r requirements.txt
flet run --web flet_gui.py
```

or just

```
python flet_gui.py
```

The page should just pop up. If not, then navigate to the URL displayed in the temrinal.

## Deploying

The entire app runs on Render. The Procfile has the start command:

```
web: uvicorn flet_gui:app --host 0.0.0.0 --port $PORT
```

Only run one instance of it. Flet keeps sessions in memory so more than one instance would break unless you set up sticky sessions :D.

## Files

```
flet_gui.py        ui and app setup
processor.py       the image modifier
assets/            boot screen assets, logo, favicon
requirements.txt   dependencies
Procfile           start command for Render
legacy/            old desktop version, not used anymore (you can still check it out if you want though)
```

The boot screen is just an index.html with a dark background and the logo. It gets served instead of the default flet one.

## Small issues

- Refreshing the page makes the websocket error out in the logs sometimes. It looks scary but it does not actually break anything.
- On a free Render instance with 512 mb of memory a really big photo can be too much. If the app keeps crashing when you run it locally (hopefully you dont have 512mb of ram), lower the MAX_PIXELS setting in flet_gui.py.
- Everything is processed on the server so big photos make the sliders a bit laggy on slow machines.
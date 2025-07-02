# reCAPit - Reflecting on Collaborative Design Processes

![Screenshot of a comment on a GitHub issue showing an image, added in the Markdown, of an Octocat smiling and raising a tentacle.](logo.png)


## About

reCAPit is an application designed for analyzing, exploring, and documenting outcomes of collaborative design processes using speech, video, gaze, and other data modalities. Its integrated visualizations provide an overview of recorded data and enable users to author visual summaries of their analysis results. Our application includes a preprocessing pipeline capable of extracting a wide range of features from the rich, multimodal data collected

## Recommendations

Our approach is best suited for collaborative workshops involving small to medium-sized groups. We recommend instrumenting the environment with a variety of data sources. Currently, we support:

* Multi-angle video recordings
* Microphones
* Mobile eye-tracking glasses
* Digital notes (taken in Microsoft Word)

We recommend the following setup:

* A shared working area where participants collect ideas using post-its, drawings, sketches, or other materials.

* A video camera positioned to capture the working area. For horizontal surfaces (e.g., tables), a top-down camera mounted on the ceiling or a tripod is ideal.

* A microphone capable of capturing speech from all participants in the room.


## Data Preparation

As described above, reCAPit supports data from multiple sensors. These data streams must be preprocessed before they can be used in the interface.

Please refer to the `processing` documentation for detailed instructions on data preprocessing.

## Installation

Ensure you have Python (version ≥ 3.10) installed. Then install all the required packages by entering the following command into your terminal. It's recommended to install the packages into new virtual environment.

`python -m pip install -r frontend/requirements.txt`

## Launching

To launch the app, navigate to the `frontend` directory and run the following command in your terminal:

`python App.py --meta [PATH_TO_META.json]`

The `meta.json` file should contain paths to the processed data sources and additional configuration information. You can use `meta_example.json` as a reference.


## Future Roadmap

We will soon release a test dataset that can be used to demo our application. Further, we plan the add following features and improvements:

- [ ] Provide installer-ready binaries for all major platforms, including Windows, macOS, and Linux

- [ ] Develop a streamlined preprocessing pipeline with a dedicated user interface to enhance accessibility

- [ ] Integrate facial detection, human trajectory tracking, and additional features into the preprocessing pipeline

## References

For more details, please refer to our forthcoming paper [link will be added soon].



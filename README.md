# Music Telepresence
Development of the audio side of the Music Telepresence Project

### This project makes use of multiple HRTF datasets in order to evaluate performance.

- MIT KEMAR dataset
  - https://sound.media.mit.edu/resources/KEMAR.html 
  - Bill Gardner <billg@media.mit.edu>
  - Keith Martin <kdm@media.mit.edu>
  - MIT Media Lab Machine Listening Group
  - May 18, 1994
- LISTEN HRTF DATABASE
  - http://recherche.ircam.fr/equipes/salles/listen/index.html

The folder structure needs to look like the following:

```
src
├── HRTFsets
│   ├── LISTEN
│   │   ├── LISTEN Dataset
│   ├── MIT
│   │   ├── MIT Dataset
│   ├── SOFA Far-Field
│   │   ├── SOFA Dataset
├── Samples 48k
│   ├── Your .wav audio samples
├── gui_audio.py
├── gui.py
├── make_binaural.py
├── readme.md 
└── .gitignore
```
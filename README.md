# plex-comskip
[![Docker Build Statu](https://img.shields.io/docker/build/boatmeme/plex-comskip.svg?style=flat-square)](https://hub.docker.com/r/boatmeme/plex-comskip/)

Inspired by Plex DVR. This container has [Comskip](https://github.com/erikkaashoek/Comskip) and [PlexComskip](https://github.com/ekim1337/PlexComskip) installed to remove commercials from any DVR'd content. Container based on [kmcgill88/k-plex](https://hub.docker.com/r/kmcgill88/k-plex/). Unlike that image, Plex is *NOT* running in this same container.

This is primarily for use in a scenario where Plex itself is installed natively on the host and the host is also running docker, such as QNAP w/Container Station.

### How to use:
- [Pull Plex-Comskip from docker](https://hub.docker.com/r/boatmeme/plex-comskip/) by running `docker pull plex-comskip`
- Download [postProcessScript.sh](https://cdn.rawgit.com/boatmeme/plex-comskip/master/postProcessScript.sh) and copy to a local path accessible to your Plex Media Server instance.
- You may need to change ownership of `postProcessScript.sh` to a plex user and make the script executable
- Go to Plex Settings, then DVR (Beta)
- DVR Settings
- Scroll to `POSTPROCESSING SCRIPT`
- Enter `/path/to/postProcessScript.sh`
- Click `Save`.
- Enjoy commercial free TV!

When DVR recordings end, `Comskip` will automatically run and the show will be added to your Plex library.

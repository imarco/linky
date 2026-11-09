# Third-party references

The reviewed upstream snapshot was `f3db92847c14245ee9afae881ecb307e27d8d829`. The controlled acquisition design was informed by [nengong/download-anything](https://github.com/nengong/download-anything): resource routing, sidecar provenance, checksum verification and explicit partial results. Its MIT notice is retained at [licenses/download-anything-MIT.txt](licenses/download-anything-MIT.txt).

Linky's acquisition implementation is independent standard-library code. No upstream runtime, credential-discovery logic, alternative-source network drivers, cloud-drive transfer, automatic unpacking, or installation skill is bundled or invoked. Keeping this notice does not imply that the upstream skill has passed any platform installation review.

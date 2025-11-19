# Explodium

A Blender N-panel add-on that shows you an exploded view of your mesh. Found under the `Edit` N-Panel.

![image](images/logo.png)

Explodium is an add-on that shows you an "exploded view" of your mesh. It temporarily separates faces from each other and expands the mesh to give you an overview of your topology. It is non-destructive and only visible while holding the assigned hotkey.
## Usage
- Select an object and change to Edit mode.
- While holding down your configured hotkey (default is Ctrl+Shift+P) to see a temporary "exploded view" of your mesh.
- Release the hotkey and the mesh returns to normal.

## Features

-  Provides an exploded view of your mesh, revealing topology, edge flow, and hidden geometry that's difficult to see in normal view.
- Customizable hotkey
- You can customize how much to shrink the mesh faces and expand the overall mesh
- You can reset default values at any time


## Screenshot
![](images/figure-1.png)
Figure 1 - In Edit mode, an exploded view of Suzanne

![](images/figure-2.png)
Figure 2 - Customizable hotkeys and explosion values

![](images/figure-3.png)
Figure 3 - A new exploded view after entering new values

## Video
![](images/figure-4.gif)
Figure 4 - Holding down the assigned hotkey (defaults to Ctrl+Shift+P but can be changed) shows an exploded view of Suzanne. You can adjust the Shrink Face and Expand Mesh values to change how much the mesh expands.

## Supported Blender Versions
Because Explodium is packaged as an Extension, it currently supports Blender 4.2+ and newer.

## Installation Options

### Blender Extensions Platform

Coming soon, hopefully...

### Install from Disk

Explodium can also be installed manually, which you can download from the [Releases](https://github.com/shawnshipley/explodium/releases) section of its [Github](https://github.com/shawnshipley/explodium) page. Just follow the steps below to install:
1. Download the latest [release](https://github.com/shawnshipley/explodium/releases)
2. In Blender, go to Edit -> Preferences
3. Click on `Get Extensions`
4. Click the Extensions Settings drop-down arrow (the small arrow in the upper right corner of the window that's facing down) and select `Install from Disk`.
![](images/figure-6.png)
5. Browse to the downloaded .zip file and select it to complete the installation.

Explodium will now show up in the `Edit` N-panel as `Explodium`.

### Changelog

#### 11/19/25 (v1.0.5)
- Initial public release
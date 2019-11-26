# Flutter Asset Monitor
Flutter asset monitor was created from the need automatically generate AssetManager class as required while building in dart. 

## Usage
./assetmon \<path to watch> \<path to write to> init(optional)
For example ./asset mon ~/AndroidStudioProjects/myproject/assets ~/AndroidStudioProjects/myproject/lib init
init should be used only when you are creating the folders. When using init, donot append your folder paths with "/".

## Dependencies:
watchdog[pip3 install watchdog] and pyperclip[pip3 install pyperclip]
### Runs on python 3.7


# Summary 
Debug Toggle Script for TypeScript Files
Toggles debug sections between commented and uncommented states.
    
## Available tags for usage in the "TypeScript" files
    - // DEBUG START [tag]
    - // DEBUG START [keep]
    - // DEBUG START [production]
    - // DEBUG START          (no tag = default)

## CLI Mode (quick operations)

```shell
# Toggle everything
python debug-toggle.py <directory>

# Comment only specific tags
python debug-toggle.py <directory> --mode comment --only keep,production

# Uncomment everything except certain tags
python debug-toggle.py <directory> --mode uncomment --except temp

# Single file
python debug-toggle.py game.ts --only performance


# Single file
python debug-toggle.py <file.ts> [--mode comment|uncomment|toggle] [--only tag1,tag2] [--except tag1,tag2]

# All file in a directory
python debug-toggle.py <directory> [--mode comment|uncomment|toggle] [--recursive] [--only tag1,tag2] [--except tag1,tag2]
```


## Watch Mode (interactive during development)

```shell
python debug-toggle.py watch <directory> --recursive
```

Then you can type commands:
```shell
> comment all
> uncomment keep,production
> toggle performance
> list              (shows all available tags)
> help              (shows commands)
> exit              (quit watch mode)
```


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


## Add the Snippet to VS Code:
1. Open VS Code
2. Press "Ctrl+Shift+P" to open the Command Palette
3. Type "Configure Snippets" and select it
4. From all the options, look for one that says "typescript" or "typescript.json".
5. Paste the snippet JSON inside the existing curly braces {}
6. Save

## How to Use the Snippet
In any `.ts` file, type one of these and press `Tab`:

### `debug` + TAB

```typescript
// DEBUG START []
|  <-- cursor here
// DEBUG END
```

### `debuglog` + TAB

```typescript
// DEBUG START []
console.log("", );
// DEBUG END
```

### `debugt` + TAB

```typescript
// DEBUG START [|]  <-- cursor here
// DEBUG END
```





#!/usr/bin/env python3

import sys
import os
import re
import time
from pathlib import Path
from typing import List, Tuple, Set, Optional
from datetime import datetime

def parse_debug_tag(line: str) -> Optional[str]:
    """Extract tag from DEBUG START line. Returns None if no tag, or the tag name."""
    match = re.search(r'//\s*DEBUG\s+START\s*\[([^\]]+)\]', line)
    if match:
        return match.group(1).strip()
    return None

def process_file(filepath: str, mode: str = 'toggle', only_tags: Set[str] = None, except_tags: Set[str] = None) -> Tuple[bool, str, Set[str]]:
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        lines = content.split('\n')
        modified_lines = []
        i = 0
        changes_made = 0
        all_tags = set()
        
        while i < len(lines):
            line = lines[i]
            
            # Check for DEBUG START
            if '// DEBUG START' in line:
                tag = parse_debug_tag(line)
                if tag:
                    all_tags.add(tag)
                
                # Check if we should process this section based on filters
                should_process = True
                if only_tags is not None:
                    should_process = tag in only_tags
                if except_tags is not None and tag in except_tags:
                    should_process = False
                
                if not should_process:
                    # Skip this section, keep as-is
                    modified_lines.append(line)
                    i += 1
                    # Copy everything until DEBUG END
                    while i < len(lines):
                        modified_lines.append(lines[i])
                        if '// DEBUG END' in lines[i]:
                            i += 1
                            break
                        i += 1
                    continue
                
                # Check if next line already has /*
                if i + 1 < len(lines) and lines[i + 1].strip() == '/*':
                    # Already commented
                    if mode == 'uncomment' or mode == 'toggle':
                        # Remove the /*
                        modified_lines.append(line)
                        i += 2  # Skip the /* line
                        changes_made += 1
                        
                        # Find and remove the matching */
                        while i < len(lines):
                            if '// DEBUG END' in lines[i]:
                                # Check if previous line has */
                                if modified_lines and modified_lines[-1].strip() == '*/':
                                    modified_lines.pop()  # Remove the */
                                modified_lines.append(lines[i])
                                i += 1
                                break
                            else:
                                modified_lines.append(lines[i])
                                i += 1
                        continue
                    else:
                        # Keep as is (already commented, mode is 'comment')
                        modified_lines.append(line)
                        i += 1
                else:
                    # Not commented yet
                    if mode == 'comment' or mode == 'toggle':
                        # Add /*
                        modified_lines.append(line)
                        modified_lines.append('/*')
                        i += 1
                        changes_made += 1
                        
                        # Find DEBUG END and add */ before it
                        while i < len(lines):
                            if '// DEBUG END' in lines[i]:
                                modified_lines.append('*/')
                                modified_lines.append(lines[i])
                                i += 1
                                break
                            else:
                                modified_lines.append(lines[i])
                                i += 1
                        continue
                    else:
                        # Keep as is (not commented, mode is 'uncomment')
                        modified_lines.append(line)
                        i += 1
            else:
                modified_lines.append(line)
                i += 1
        
        new_content = '\n'.join(modified_lines)
        
        if new_content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            return True, f"✓ Modified: {filepath} ({changes_made} debug section(s) toggled)", all_tags
        else:
            return True, f"○ No changes needed: {filepath}", all_tags
            
    except Exception as e:
        return False, f"✗ Error processing {filepath}: {str(e)}", set()

def get_ts_files(directory: str, recursive: bool = False, file_filter: Set[str] = None) -> List[Path]:
    """Get list of .ts files, optionally filtered."""
    path = Path(directory)
    
    if not path.is_dir():
        return []
    
    pattern = "**/*.ts" if recursive else "*.ts"
    all_files = list(path.glob(pattern))
    
    if file_filter:
        # Filter files based on the filter set
        filtered = []
        for f in all_files:
            # Check if filename matches any filter
            filename = f.name
            rel_path = str(f.relative_to(path))
            
            for filter_item in file_filter:
                if filter_item in [filename, rel_path, str(f)]:
                    filtered.append(f)
                    break
        return filtered
    
    return all_files

def process_directory(directory: str, mode: str = 'toggle', recursive: bool = False, 
                     only_tags: Set[str] = None, except_tags: Set[str] = None,
                     file_filter: Set[str] = None) -> Tuple[int, Set[str]]:
    """Process all .ts files in a directory. Returns (success_count, all_tags)"""
    ts_files = get_ts_files(directory, recursive, file_filter)
    
    if not ts_files:
        print(f"No .ts files found")
        return 0, set()
    
    print(f"Processing {len(ts_files)} TypeScript file(s)...\n")
    
    success_count = 0
    all_tags = set()
    for ts_file in ts_files:
        success, message, file_tags = process_file(str(ts_file), mode, only_tags, except_tags)
        print(message)
        all_tags.update(file_tags)
        if success:
            success_count += 1
    
    print(f"\n{success_count}/{len(ts_files)} files processed successfully")
    return success_count, all_tags

def parse_watch_command(cmd: str) -> dict:
    result = {
        'action': None,
        'tags': None,  # None means all
        'files': None,  # None means all
        'except_tags': None
    }
    
    # Split by 'in' and 'except' keywords
    parts = cmd.lower().split(' in ')
    main_part = parts[0].strip()
    
    file_and_except = None
    if len(parts) > 1:
        file_and_except = parts[1].strip()
    
    # Parse main part (action + tags)
    main_tokens = main_part.split(maxsplit=1)
    if len(main_tokens) < 1:
        return result
    
    result['action'] = main_tokens[0]
    
    if len(main_tokens) > 1:
        tag_part = main_tokens[1]
        if tag_part != 'all':
            result['tags'] = set(t.strip() for t in tag_part.split(','))
    
    # Parse file and except parts
    if file_and_except:
        if ' except ' in file_and_except:
            file_part, except_part = file_and_except.split(' except ', 1)
            result['files'] = set(f.strip() for f in file_part.split(','))
            result['except_tags'] = set(t.strip() for t in except_part.split(','))
        else:
            result['files'] = set(f.strip() for f in file_and_except.split(','))
    
    # Check for except in main part (e.g., "comment all except tag1")
    if ' except ' in main_part and result['except_tags'] is None:
        main_part, except_part = main_part.split(' except ', 1)
        result['except_tags'] = set(t.strip() for t in except_part.split(','))
        # Re-parse main part
        main_tokens = main_part.split(maxsplit=1)
        result['action'] = main_tokens[0]
        if len(main_tokens) > 1 and main_tokens[1] != 'all':
            result['tags'] = set(t.strip() for t in main_tokens[1].split(','))
    
    return result

def watch_mode(directory: str, recursive: bool = False):
    """Interactive watch mode for processing files."""
    print(f"=== Debug Toggle - Watch Mode ===")
    print(f"Watching: {directory}")
    print(f"Recursive: {recursive}")
    print(f"\n📖 Command Syntax:")
    print(f"  <action> [tags] [in files] [except tags]")
    print(f"\n🎯 Examples:")
    print(f"  comment all")
    print(f"  uncomment keep,production")
    print(f"  toggle performance in game.ts")
    print(f"  comment all in player.ts,enemy.ts")
    print(f"  uncomment keep in game.ts except temp")
    print(f"  toggle all except debug")
    print(f"\n⚙️  Other Commands:")
    print(f"  list                - List all available tags")
    print(f"  list in file.ts     - List tags in specific file(s)")
    print(f"  files               - List all .ts files")
    print(f"  help                - Show this help")
    print(f"  exit                - Exit watch mode")
    print(f"\nReady for commands...\n")
    
    while True:
        try:
            cmd = input("> ").strip()
            
            if not cmd:
                continue
            
            cmd_lower = cmd.lower()
            
            if cmd_lower in ['exit', 'quit', 'q']:
                print("Exiting watch mode...")
                break
            
            if cmd_lower == 'help':
                print("\n📖 Command Syntax:")
                print("  <action> [tags] [in files] [except tags]")
                print("\n  Actions: comment, uncomment, toggle")
                print("  Tags: 'all' or comma-separated tags (e.g., keep,production)")
                print("  Files: comma-separated filenames (e.g., game.ts,player.ts)")
                print("\n🎯 Examples:")
                print("  comment all")
                print("  uncomment keep,production")
                print("  toggle performance in game.ts")
                print("  comment all in player.ts,enemy.ts")
                print("  uncomment keep in game.ts except temp")
                print("  toggle all except debug")
                print("\n⚙️  Other Commands:")
                print("  list [in files]     - List tags")
                print("  files               - List .ts files")
                print("  help                - Show help")
                print("  exit                - Exit\n")
                continue
            
            if cmd_lower == 'files':
                print("\n📁 TypeScript files:")
                ts_files = get_ts_files(directory, recursive)
                if ts_files:
                    for f in sorted(ts_files):
                        rel_path = f.relative_to(Path(directory))
                        print(f"  • {rel_path}")
                    print(f"\nTotal: {len(ts_files)} files")
                else:
                    print("  No .ts files found")
                print()
                continue
            
            if cmd_lower.startswith('list'):
                file_filter = None
                if ' in ' in cmd_lower:
                    _, files_part = cmd_lower.split(' in ', 1)
                    file_filter = set(f.strip() for f in files_part.split(','))
                
                print("\n🔍 Scanning for tags...")
                ts_files = get_ts_files(directory, recursive, file_filter)
                
                if not ts_files:
                    print("No .ts files found")
                    print()
                    continue
                
                all_tags = set()
                file_tags_map = {}
                
                for ts_file in ts_files:
                    _, _, tags = process_file(str(ts_file), mode='toggle', 
                                             only_tags=set(), except_tags=set(['__dummy__']))
                    if tags:
                        rel_path = ts_file.relative_to(Path(directory))
                        file_tags_map[str(rel_path)] = tags
                        all_tags.update(tags)
                
                if all_tags:
                    print(f"\n🏷️  All tags: {', '.join(sorted(all_tags))}\n")
                    if file_tags_map:
                        print("📄 Tags by file:")
                        for filepath, tags in sorted(file_tags_map.items()):
                            print(f"  • {filepath}: {', '.join(sorted(tags))}")
                else:
                    print("\nNo tags found in debug sections")
                print()
                continue
            
            # Parse and execute action command
            parsed = parse_watch_command(cmd)
            
            if parsed['action'] not in ['comment', 'uncomment', 'toggle']:
                print(f"❌ Unknown command. Type 'help' for available commands.\n")
                continue
            
            # Build description
            desc_parts = [parsed['action']]
            if parsed['tags']:
                desc_parts.append(f"tags: {', '.join(sorted(parsed['tags']))}")
            else:
                desc_parts.append("all tags")
            
            if parsed['files']:
                desc_parts.append(f"in: {', '.join(sorted(parsed['files']))}")
            else:
                desc_parts.append("in: all files")
            
            if parsed['except_tags']:
                desc_parts.append(f"except: {', '.join(sorted(parsed['except_tags']))}")
            
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Executing: {' | '.join(desc_parts)}")
            
            success_count, all_tags = process_directory(
                directory, 
                mode=parsed['action'], 
                recursive=recursive, 
                only_tags=parsed['tags'],
                except_tags=parsed['except_tags'],
                file_filter=parsed['files']
            )
            print()
            
        except KeyboardInterrupt:
            print("\n\nExiting watch mode...")
            break
        except EOFError:
            print("\n\nExiting watch mode...")
            break
        except Exception as e:
            print(f"❌ Error: {str(e)}\n")

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    # Check for watch mode
    if sys.argv[1] == 'watch':
        if len(sys.argv) < 3:
            print("Error: watch mode requires a directory")
            print("Usage: python debug_toggle.py watch <directory> [--recursive]")
            sys.exit(1)
        
        directory = sys.argv[2]
        recursive = '--recursive' in sys.argv or '-r' in sys.argv
        
        if not os.path.isdir(directory):
            print(f"Error: {directory} is not a directory")
            sys.exit(1)
        
        watch_mode(directory, recursive)
        sys.exit(0)
    
    # CLI mode
    target = sys.argv[1]
    mode = 'toggle'
    recursive = False
    only_tags = None
    except_tags = None
    
    # Parse arguments
    if '--mode' in sys.argv:
        mode_index = sys.argv.index('--mode')
        if mode_index + 1 < len(sys.argv):
            mode = sys.argv[mode_index + 1]
            if mode not in ['comment', 'uncomment', 'toggle']:
                print("Error: mode must be 'comment', 'uncomment', or 'toggle'")
                sys.exit(1)
    
    if '--recursive' in sys.argv or '-r' in sys.argv:
        recursive = True
    
    if '--only' in sys.argv:
        only_index = sys.argv.index('--only')
        if only_index + 1 < len(sys.argv):
            only_tags = set(tag.strip() for tag in sys.argv[only_index + 1].split(','))
    
    if '--except' in sys.argv:
        except_index = sys.argv.index('--except')
        if except_index + 1 < len(sys.argv):
            except_tags = set(tag.strip() for tag in sys.argv[except_index + 1].split(','))
    
    # Process target
    if os.path.isfile(target):
        if not target.endswith('.ts'):
            print("Error: File must be a .ts file")
            sys.exit(1)
        success, message, tags = process_file(target, mode, only_tags, except_tags)
        print(message)
        if tags:
            print(f"Tags found: {', '.join(sorted(tags))}")
        sys.exit(0 if success else 1)
    elif os.path.isdir(target):
        success_count, tags = process_directory(target, mode, recursive, only_tags, except_tags)
        if tags:
            print(f"\nAll tags found: {', '.join(sorted(tags))}")
        sys.exit(0 if success_count > 0 else 1)
    else:
        print(f"Error: {target} not found")
        sys.exit(1)

if __name__ == "__main__":
    main()

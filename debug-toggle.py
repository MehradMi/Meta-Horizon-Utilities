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

def process_directory(directory: str, mode: str = 'toggle', recursive: bool = False, 
                     only_tags: Set[str] = None, except_tags: Set[str] = None) -> Tuple[int, Set[str]]:
    """Process all .ts files in a directory. Returns (success_count, all_tags)"""
    path = Path(directory)
    
    if not path.is_dir():
        print(f"Error: {directory} is not a directory")
        return 0, set()
    
    pattern = "**/*.ts" if recursive else "*.ts"
    ts_files = list(path.glob(pattern))
    
    if not ts_files:
        print(f"No .ts files found in {directory}")
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

def watch_mode(directory: str, recursive: bool = False):
    """Interactive watch mode for processing files."""
    print(f"=== Debug Toggle - Watch Mode ===")
    print(f"Watching: {directory}")
    print(f"Recursive: {recursive}")
    print(f"\nAvailable commands:")
    print(f"  comment [all|tag1,tag2]     - Comment out debug sections")
    print(f"  uncomment [all|tag1,tag2]   - Uncomment debug sections")
    print(f"  toggle [all|tag1,tag2]      - Toggle debug sections")
    print(f"  list                        - List all available tags")
    print(f"  status                      - Show current status")
    print(f"  help                        - Show this help")
    print(f"  exit                        - Exit watch mode")
    print(f"\nExamples:")
    print(f"  > comment all")
    print(f"  > uncomment keep,production")
    print(f"  > toggle performance")
    print(f"\nReady for commands...\n")
    
    while True:
        try:
            cmd = input("> ").strip().lower()
            
            if not cmd:
                continue
            
            if cmd in ['exit', 'quit', 'q']:
                print("Exiting watch mode...")
                break
            
            if cmd == 'help':
                print("\nCommands:")
                print("  comment [all|tag1,tag2]   - Comment debug sections")
                print("  uncomment [all|tag1,tag2] - Uncomment debug sections")
                print("  toggle [all|tag1,tag2]    - Toggle debug sections")
                print("  list                      - List all tags")
                print("  status                    - Show status")
                print("  exit                      - Exit\n")
                continue
            
            if cmd == 'list':
                print("\nScanning for tags...")
                _, all_tags = process_directory(directory, mode='toggle', recursive=recursive, 
                                               only_tags=set(), except_tags=set(['__dummy__']))
                if all_tags:
                    print(f"\nFound tags: {', '.join(sorted(all_tags))}")
                else:
                    print("\nNo tags found in debug sections")
                print()
                continue
            
            if cmd == 'status':
                print("\n[Status information not implemented yet - shows which sections are commented]")
                print()
                continue
            
            # Parse command and tags
            parts = cmd.split(maxsplit=1)
            if len(parts) < 2:
                print("Error: Please specify 'all' or tag names (e.g., 'comment all' or 'toggle keep,production')\n")
                continue
            
            action = parts[0]
            target = parts[1]
            
            if action not in ['comment', 'uncomment', 'toggle']:
                print(f"Error: Unknown command '{action}'. Type 'help' for available commands.\n")
                continue
            
            only_tags = None
            if target != 'all':
                only_tags = set(tag.strip() for tag in target.split(','))
            
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Executing: {action} {target}")
            success_count, all_tags = process_directory(directory, mode=action, recursive=recursive, only_tags=only_tags)
            print()
            
        except KeyboardInterrupt:
            print("\n\nExiting watch mode...")
            break
        except EOFError:
            print("\n\nExiting watch mode...")
            break
        except Exception as e:
            print(f"Error: {str(e)}\n")

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

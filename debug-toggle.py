#!/usr/bin/env python3

import sys
import os
import re
from pathlib import Path
from typing import List, Tuple

def process_file(filepath: str, mode: str = 'toggle') -> Tuple[bool, str]:
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        lines = content.split('\n')
        modified_lines = []
        i = 0
        changes_made = 0
        
        while i < len(lines):
            line = lines[i]
            
            # Check for DEBUG START
            if '// DEBUG START' in line:
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
            return True, f"✓ Modified: {filepath} ({changes_made} debug section(s) toggled)"
        else:
            return True, f"○ No changes needed: {filepath}"
            
    except Exception as e:
        return False, f"✗ Error processing {filepath}: {str(e)}"

def process_directory(directory: str, mode: str = 'toggle', recursive: bool = False) -> None:
    path = Path(directory)
    
    if not path.is_dir():
        print(f"Error: {directory} is not a directory")
        return
    
    pattern = "**/*.ts" if recursive else "*.ts"
    ts_files = list(path.glob(pattern))
    
    if not ts_files:
        print(f"No .ts files found in {directory}")
        return
    
    print(f"Processing {len(ts_files)} TypeScript file(s)...\n")
    
    success_count = 0
    for ts_file in ts_files:
        success, message = process_file(str(ts_file), mode)
        print(message)
        if success:
            success_count += 1
    
    print(f"\n{success_count}/{len(ts_files)} files processed successfully")

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    target = sys.argv[1]
    mode = 'toggle'
    recursive = False
    
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
    
    # Process target
    if os.path.isfile(target):
        if not target.endswith('.ts'):
            print("Error: File must be a .ts file")
            sys.exit(1)
        success, message = process_file(target, mode)
        print(message)
        sys.exit(0 if success else 1)
    elif os.path.isdir(target):
        process_directory(target, mode, recursive)
    else:
        print(f"Error: {target} not found")
        sys.exit(1)

if __name__ == "__main__":
    main()

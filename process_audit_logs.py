import os
import re
import csv

def process_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f.readlines()]

    # Use a dictionary to store results, ensuring unique computer names
    results_dict = {}
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Check for "Local System" entries
        if "Local System" in line:
            fields = line.split('\t')
            computer_name = fields[0].strip()
            if computer_name not in results_dict:  # Only process if not already added
                json_index = i + 3
                if json_index < len(lines) and lines[json_index].startswith('{') and lines[json_index].endswith('}'):
                    json_line = lines[json_index]
                    return_code_match = re.search(r'"returnCode":(\d+)', json_line)
                    return_reason_match = re.search(r'"returnReason":"(.*?)"(?=,"logging":)', json_line)
                    
                    if return_code_match:
                        return_code = return_code_match.group(1)
                        if return_code == "0":
                            upgrade_status = "Pass"
                            reason = ""
                        elif return_code == "1":
                            upgrade_status = "Fail"
                            reason = return_reason_match.group(1) if return_reason_match else "Unknown reason"
                        else:
                            upgrade_status = "Fail"
                            reason = "Invalid returnCode"
                    else:
                        upgrade_status = "Fail"
                        reason = "Parsing error"
                else:
                    upgrade_status = "Unknown"  # Changed to "Unknown" per your request
                    reason = "Execution error"
                results_dict[computer_name] = [upgrade_status, reason]
            i += 1
        
        # Check for "Expired" entries
        elif "Expired" in line:
            fields = line.split('\t')
            if len(fields) >= 5 and fields[4] == "Expired":
                computer_name = fields[0].strip()
                if computer_name not in results_dict:  # Only process if not already added
                    upgrade_status = "Unknown"
                    reason = "Computer was shutdown or unreachable"
                    results_dict[computer_name] = [upgrade_status, reason]
            i += 1
        
        # Check for "In progress" entries
        elif "In progress" in line:
            if i > 0:  # Ensure there is a previous line
                prev_line = lines[i - 1]
                if "--" in prev_line:
                    computer_name = prev_line.split("--")[0].strip()
                    if computer_name not in results_dict:  # Only process if not already added
                        upgrade_status = "Unknown"
                        reason = "Computer was shutdown or unreachable"
                        results_dict[computer_name] = [upgrade_status, reason]
            i += 1
        
        # Check "Task" or "End" lines
        elif line.startswith("Task") or line.startswith("End"):
            if i > 0:
                prev_line = lines[i - 1]
                fields = prev_line.split('\t')
                if len(fields) >= 5 and fields[4] == "Expired":
                    computer_name = fields[0].strip()
                    if computer_name not in results_dict:  # Only process if not already added
                        upgrade_status = "Unknown"
                        reason = "Computer was shutdown or unreachable"
                        results_dict[computer_name] = [upgrade_status, reason]
            i += 1
        else:
            i += 1

    # Convert dictionary to list of lists for CSV writing
    return [[computer_name, status, reason] for computer_name, [status, reason] in results_dict.items()]

def main():
    # Get the directory where the script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # List all .txt files in the directory
    txt_files = [f for f in os.listdir(script_dir) if f.endswith('.txt')]
    
    # Check if there are any .txt files
    if not txt_files:
        print("No .txt files found in the directory.")
        return
    
    # Define the single output CSV file
    output_csv = os.path.join(script_dir, "combined_results.csv")
    
    # Open the CSV file once and write all data
    with open(output_csv, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        # Process each text file
        for txt_file in txt_files:
            print(f"Processing file: {txt_file}")
            file_path = os.path.join(script_dir, txt_file)
            # Get results for the current file
            file_results = process_file(file_path)
            # Get the base name of the text file (without .txt)
            base_name = os.path.splitext(txt_file)[0]
            # Write two blank rows before the base name
            writer.writerow([])
            writer.writerow([])
            # Write the base name
            writer.writerow([base_name])
            # Write the header
            writer.writerow(["Computer Name", "Upgrade Status", "Reason"])
            # Write the data rows for this file
            writer.writerows(file_results)
    
    print(f"All results written to {output_csv}")

if __name__ == "__main__":
    main()
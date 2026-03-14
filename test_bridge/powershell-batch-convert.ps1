# Get the script directory (same as PhysicsTool.exe)
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$PhysicsTool = Join-Path -Path $ScriptDir -ChildPath "PhysicsTool.exe"

# Prompt user for the input folder containing .bin files
$InputDir = Read-Host "Enter the full path to the input folder (where .bin files are located)"

# Ensure input directory exists
if (!(Test-Path -Path $InputDir)) {
    Write-Host "Error: Input directory does not exist. Exiting."
    exit 1
}

# Define output directory inside the input directory
$OutputDir = Join-Path -Path $InputDir -ChildPath "output"

# Create the output directory if it does not exist
if (!(Test-Path -Path $OutputDir)) {
    Write-Host "Creating output directory: $OutputDir"
    New-Item -ItemType Directory -Path $OutputDir | Out-Null
}

# Get all .bin files in the input directory
$Files = Get-ChildItem -Path $InputDir -Filter "*.bin" -File

# Check if there are files to process
if ($Files.Count -eq 0) {
    Write-Host "No .bin files found in input directory: $InputDir"
    exit 1
}

# Process each .bin file and output as .xml inside the "output" folder
foreach ($File in $Files) {
    $InputFile = $File.FullName
    $OutputFileName = [System.IO.Path]::GetFileNameWithoutExtension($File.Name) + ".xml"
    $OutputFile = Join-Path -Path $OutputDir -ChildPath $OutputFileName

    Write-Host "Processing: $InputFile -> $OutputFile"

    # Run PhysicsTool.exe
    try {
        Start-Process -FilePath $PhysicsTool -ArgumentList "`"$InputFile`" `"$OutputFile`"" -NoNewWindow -Wait
        Write-Host "Success: Converted $File.Name to $OutputFileName."
    } catch {
        Write-Host "Error processing $File.Name - $_"
    }
}

Write-Host "Batch processing complete. Converted files are saved in: $OutputDir"

Add-Type -AssemblyName System.Windows.Forms

# Create Form
$Form = New-Object System.Windows.Forms.Form
$Form.Text = "pommelstrike .bin to .xml Converter"
$Form.Size = New-Object System.Drawing.Size(400,250)
$Form.StartPosition = "CenterScreen"

# Label - Instruction
$Label = New-Object System.Windows.Forms.Label
$Label.Text = "Select Input Folder:"
$Label.Location = New-Object System.Drawing.Point(10,20)
$Label.Size = New-Object System.Drawing.Size(120,20)
$Form.Controls.Add($Label)

# TextBox - Input Folder
$InputBox = New-Object System.Windows.Forms.TextBox
$InputBox.Location = New-Object System.Drawing.Point(10,50)
$InputBox.Size = New-Object System.Drawing.Size(280,20)
$Form.Controls.Add($InputBox)

# Button - Browse
$BrowseButton = New-Object System.Windows.Forms.Button
$BrowseButton.Text = "Browse"
$BrowseButton.Location = New-Object System.Drawing.Point(300,50)
$BrowseButton.Size = New-Object System.Drawing.Size(70,25)
$Form.Controls.Add($BrowseButton)

# Progress Bar
$ProgressBar = New-Object System.Windows.Forms.ProgressBar
$ProgressBar.Location = New-Object System.Drawing.Point(10, 120)
$ProgressBar.Size = New-Object System.Drawing.Size(360, 20)
$ProgressBar.Style = "Continuous"
$Form.Controls.Add($ProgressBar)

# Convert Button
$ConvertButton = New-Object System.Windows.Forms.Button
$ConvertButton.Text = "Convert"
$ConvertButton.Location = New-Object System.Drawing.Point(150, 160)
$ConvertButton.Size = New-Object System.Drawing.Size(100,30)
$Form.Controls.Add($ConvertButton)

# Folder Dialog
$FolderDialog = New-Object System.Windows.Forms.FolderBrowserDialog

# Browse Button Action
$BrowseButton.Add_Click({
    if ($FolderDialog.ShowDialog() -eq "OK") {
        $InputBox.Text = $FolderDialog.SelectedPath
    }
})

# Convert Button Action
$ConvertButton.Add_Click({
    $InputDir = $InputBox.Text

    if (!(Test-Path -Path $InputDir)) {
        [System.Windows.Forms.MessageBox]::Show("Error: Input directory does not exist.", "Error", "OK", "Error")
        return
    }

    # Define output directory inside input folder
    $OutputDir = Join-Path -Path $InputDir -ChildPath "output"

    if (!(Test-Path -Path $OutputDir)) {
        New-Item -ItemType Directory -Path $OutputDir | Out-Null
    }

    # Get all .bin files
    $Files = Get-ChildItem -Path $InputDir -Filter "*.bin" -File

    if ($Files.Count -eq 0) {
        [System.Windows.Forms.MessageBox]::Show("No .bin files found!", "Warning", "OK", "Warning")
        return
    }

    $TotalFiles = $Files.Count
    $CurrentFile = 0

    foreach ($File in $Files) {
        $InputFile = $File.FullName
        $OutputFile = Join-Path -Path $OutputDir -ChildPath ([System.IO.Path]::GetFileNameWithoutExtension($File.Name) + ".xml")

        Start-Process -FilePath "$PSScriptRoot\PhysicsTool.exe" -ArgumentList "`"$InputFile`" `"$OutputFile`"" -NoNewWindow -Wait

        $CurrentFile++
        $ProgressBar.Value = ($CurrentFile / $TotalFiles) * 100
    }

    [System.Windows.Forms.MessageBox]::Show("Conversion Complete!", "Success", "OK", "Information")
})

# Show Form
$Form.ShowDialog()

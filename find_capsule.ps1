Add-Type -AssemblyName System.Drawing
$refFile = "C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6\.user_uploaded\media_1792922507504_d96a1582.png"
$img = [System.Drawing.Bitmap]::FromFile($refFile)

# Find bounding box of search bar background (approx rgb(240-245, 230-238, 220-230))
$capsulePixels = @()
for ($y = 0; $y -lt 150; $y++) {
    for ($x = 0; $x -lt $img.Width; $x++) {
        $c = $img.GetPixel($x, $y)
        if ($c.R -gt 230 -and $c.R -lt 250 -and $c.G -gt 225 -and $c.G -lt 242 -and $c.B -gt 215 -and $c.B -lt 235) {
            $capsulePixels += [PSCustomObject]@{ X = $x; Y = $y; R = $c.R; G = $c.G; B = $c.B }
        }
    }
}

if ($capsulePixels.Count -gt 0) {
    $minX = ($capsulePixels | Measure-Object -Property X -Minimum).Minimum
    $maxX = ($capsulePixels | Measure-Object -Property X -Maximum).Maximum
    $minY = ($capsulePixels | Measure-Object -Property Y -Minimum).Minimum
    $maxY = ($capsulePixels | Measure-Object -Property Y -Maximum).Maximum
    Write-Output "Search capsule found: X from $minX to $maxX, Y from $minY to $maxY. Width: $($maxX - $minX), Height: $($maxY - $minY)"
} else {
    Write-Output "No capsule pixels matched."
}

$img.Dispose()

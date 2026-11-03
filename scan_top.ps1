Add-Type -AssemblyName System.Drawing
$bmp = New-Object System.Drawing.Bitmap("scratch\top_bar.png")

# Scan every 5 pixels
for ($x = 0; $x -lt $bmp.Width; $x += 10) {
    for ($y = 0; $y -lt $bmp.Height; $y += 5) {
        $c = $bmp.GetPixel($x, $y)
        if ($c.R -lt 120 -and $c.G -lt 120 -and $c.B -lt 120) {
            Write-Output "Dark pixel at X=$x, Y=$y (R=$($c.R), G=$($c.G), B=$($c.B))"
            break
        }
    }
}
$bmp.Dispose()

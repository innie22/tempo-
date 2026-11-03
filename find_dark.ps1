Add-Type -AssemblyName System.Drawing
$bmp = New-Object System.Drawing.Bitmap("scratch\ref2_search_bar_exact.png")

# Let's inspect the icon location and text location in ref2
# The capsule background is around Y=10 to Y=60. Let's check non-capsule, dark pixels in this range.
for ($x = 0; $x -lt $bmp.Width; $x += 10) {
    for ($y = 10; $y -lt 60; $y += 5) {
        $c = $bmp.GetPixel($x, $y)
        if ($c.R -lt 160 -and $c.G -lt 160 -and $c.B -lt 160) {
            Write-Output "Dark pixel at X=$x, Y=$y (R=$($c.R), G=$($c.G), B=$($c.B))"
            break
        }
    }
}
$bmp.Dispose()

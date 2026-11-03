Add-Type -AssemblyName System.Drawing
$bmp = New-Object System.Drawing.Bitmap("scratch\ref_search_bar.png")
Write-Output "Crop size: $($bmp.Width) x $($bmp.Height)"

# Find dark pixels (< 150)
$darkCols = @{}
for ($x = 0; $x -lt $bmp.Width; $x++) {
    $count = 0
    for ($y = 0; $y -lt $bmp.Height; $y++) {
        $c = $bmp.GetPixel($x, $y)
        if ($c.R -lt 150 -and $c.G -lt 150 -and $c.B -lt 150) {
            $count++
        }
    }
    if ($count -gt 2) {
        $darkCols[$x] = $count
    }
}
$sortedKeys = $darkCols.Keys | Sort-Object
Write-Output "First dark column X: $($sortedKeys[0]), Last dark column X: $($sortedKeys[-1])"
Write-Output "Columns with dark pixels: $($sortedKeys -join ', ')"
$bmp.Dispose()

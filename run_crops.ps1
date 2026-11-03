
Add-Type -AssemblyName System.Drawing
$refFile = "C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6\.user_uploaded\media_1792922507504_d96a1582.png"
$img = [System.Drawing.Bitmap]::FromFile($refFile)
Write-Output "Dimensions: $($img.Width) x $($img.Height)"

# In Reference 2, the search bar is between the left nav and right edge
# Let's crop from Y=30 to Y=120, X=200 to X=950
$rect = New-Object System.Drawing.Rectangle(200, 30, 750, 80)
$bmp = New-Object System.Drawing.Bitmap($rect.Width, $rect.Height)
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.DrawImage($img, (New-Object System.Drawing.Rectangle(0, 0, $rect.Width, $rect.Height)), $rect, [System.Drawing.GraphicsUnit]::Pixel)
$bmp.Save("C:\Users\YEN NHI\OneDrive\Tài liệu\GitHub\tempo-\scratch\ref2_crop_exact.png", [System.Drawing.Imaging.ImageFormat]::Png)

# Let's also check Reference 4 (Posts)
$ref4 = "C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6\.user_uploaded\media_1792922507475_44bad35c.png"
$img4 = [System.Drawing.Bitmap]::FromFile($ref4)
$bmp4 = New-Object System.Drawing.Bitmap(750, 80)
$g4 = [System.Drawing.Graphics]::FromImage($bmp4)
$g4.DrawImage($img4, (New-Object System.Drawing.Rectangle(0, 0, 750, 80)), $rect, [System.Drawing.GraphicsUnit]::Pixel)
$bmp4.Save("C:\Users\YEN NHI\OneDrive\Tài liệu\GitHub\tempo-\scratch\ref4_crop_exact.png", [System.Drawing.Imaging.ImageFormat]::Png)

$g.Dispose(); $bmp.Dispose(); $img.Dispose()
$g4.Dispose(); $bmp4.Dispose(); $img4.Dispose()
Write-Output "Successfully saved crops."

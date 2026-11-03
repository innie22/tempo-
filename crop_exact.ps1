Add-Type -AssemblyName System.Drawing
$refFile = "C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6\.user_uploaded\media_1792922507504_d96a1582.png"
$img = [System.Drawing.Bitmap]::FromFile($refFile)

# Let's crop X=200..920, Y=20..120
$rect = New-Object System.Drawing.Rectangle(200, 20, 720, 100)
$bmp = New-Object System.Drawing.Bitmap($rect.Width, $rect.Height)
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.DrawImage($img, (New-Object System.Drawing.Rectangle(0, 0, $rect.Width, $rect.Height)), $rect, [System.Drawing.GraphicsUnit]::Pixel)
$bmp.Save("scratch\ref2_search_bar_exact.png", [System.Drawing.Imaging.ImageFormat]::Png)

# Let's also do Reference 4 (Posts)
$ref4File = "C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6\.user_uploaded\media_1792922507475_44bad35c.png"
$img4 = [System.Drawing.Bitmap]::FromFile($ref4File)
$bmp4 = New-Object System.Drawing.Bitmap(720, 100)
$g4 = [System.Drawing.Graphics]::FromImage($bmp4)
$g4.DrawImage($img4, (New-Object System.Drawing.Rectangle(0, 0, 720, 100)), $rect, [System.Drawing.GraphicsUnit]::Pixel)
$bmp4.Save("scratch\ref4_search_bar_exact.png", [System.Drawing.Imaging.ImageFormat]::Png)

$g.Dispose(); $bmp.Dispose(); $img.Dispose()
$g4.Dispose(); $bmp4.Dispose(); $img4.Dispose()
Write-Output "Saved ref2 and ref4 crops"

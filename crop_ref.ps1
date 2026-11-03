Add-Type -AssemblyName System.Drawing
$refFile = "C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6\.user_uploaded\media_1792922507504_d96a1582.png"
$img = [System.Drawing.Image]::FromFile($refFile)
Write-Output "Dimensions: $($img.Width) x $($img.Height)"

# The main content search bar is in the top right area of the page.
# Let's crop from X=250 to X=img.Width-50, Y=20 to Y=120
$cropW = $img.Width - 300
$cropH = 100
$rect = New-Object System.Drawing.Rectangle(250, 20, $cropW, $cropH)
$bmp = New-Object System.Drawing.Bitmap($rect.Width, $rect.Height)
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.DrawImage($img, (New-Object System.Drawing.Rectangle(0, 0, $rect.Width, $rect.Height)), $rect, [System.Drawing.GraphicsUnit]::Pixel)
$bmp.Save("scratch\ref_search_bar.png", [System.Drawing.Imaging.ImageFormat]::Png)
$g.Dispose()
$bmp.Dispose()
$img.Dispose()
Write-Output "Crop saved: scratch\ref_search_bar.png"

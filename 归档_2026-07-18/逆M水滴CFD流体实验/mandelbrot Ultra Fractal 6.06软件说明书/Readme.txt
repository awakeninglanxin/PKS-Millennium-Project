Ultra Fractal 6 Readme
----------------------

Version:     6.06
Build date:  January 26, 2024


* Disclaimer

I, FREDERIK SLIJKERMAN, THE AUTHOR OF ULTRA FRACTAL, SPECIFICALLY DISCLAIM ALL WARRANTIES, EXPRESSED OR IMPLIED, INCLUDING BUT NOT LIMITED TO, IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE. IN NO EVENT SHALL I BE LIABLE FOR ANY DAMAGE ULTRA FRACTAL MAY CAUSE, INCLUDING BUT NOT LIMITED TO SPECIAL, INCIDENTAL, CONSEQUENTIAL OR OTHER DAMAGES.


* What's new in Ultra Fractal 6.06?

Added native version for Apple Silicon Macs, so the Rosetta 2 translation layer is no longer needed. This ensures Ultra Fractal runs optimally on all new Macs using the M1 and later processors.

Fixed a compiler bug that prevented functions from returning a literal complex value directly.

Fixed incorrect icons in the interpolation drop-down box in the Timeline tool window.

Fixed bug that prevented copying and pasting in the Find/Replace dialog for the formula editor on Windows.


* What's new in Ultra Fractal 6.05?

Improved the anti-aliasing algorithm used by the Render to Disk feature to produce better results and take less CPU time, especially with Depth settings larger than 1.

Docked Mode tool windows now only show the mode of the fractal window they belong to, which fixes problems with e.g. Explore mode and multiple fractal windows.

The maximized state of fractal windows, formula editors, and browsers is now restored when reopening a file or window. (Previously windows would never restore as maximized.)

Previews in eyedropper mode now get a higher calculation priority, so they also work well if the fractal is currently calculating.

Fixed a bug that caused the frame input in the animation bar to be invisible on Windows (since version 6.04).

Fixed a bug that could cause the network server application on Mac to prematurely stop calculating, as well as possible issues when using multiple connections to the same server.

Double-clicking a float value in an edit control now also includes the sign in the selection on Windows.

Implemented Esc shortcut to cancel the eyedropper.

Changing monitors (e.g. unplugging an external monitor) could previously cause floating tool windows to become invisible: this is now fixed.

Fixed a bug in the browser that would cause all formula thumbnails except the first to have the default aspect ratio.

Fixed a bug that caused the Previous/Next Frame keyboard shortcuts not to work on Mac.

Fixed a bug that prevented touch gestures for zooming, rotating and panning (e.g. on a trackpad) from working on Mac.

Fixed various minor visual issues on both Windows and Mac.

Small bug fixes and improvements.


* What's new in Ultra Fractal 6.04?

Fixed a crash with some graphics drivers on Windows with OpenGL acceleration enabled.

Fixed various issues on Windows with 150% DPI scaling.

Fixed various problems in macOS 11 (Big Sur): the buttons in the layers list wouldn't turn off, and items in some lists were not drawn correctly.

Improved color matching in the fractal window on macOS on some monitors.

Fixed a problem when running in full screen mode on macOS (via the green window button): opening a modal browser (e.g. to select a formula) could lead to a non-functioning interface.

The welcome and evaluation dialogs now appear correctly in Dark Mode on macOS.


* What’s new in Ultra Fractal 6.03?

Added support for Dark Mode on macOS Mojave and Catalina.

Fixed problems with exporting as a Quicktime movie on macOS Catalina.

Changed the default syntax highlighting colors in the formula editor so all elements look good both in light and dark user interface modes.

Fixed a bug that could cause unfinished strips to appear in the final image when using multi-pass or guessing, especially when using many calculation threads.

Fixed a possible crash when using formula plug-ins in arbitrary precision mode.

Fixed a bug when dragging a layer group to another fractal window: if the layers within the group were selected as well, they would be copied twice.

Fixed a bug that caused the precision setting to be ignored for fractal formulas. Added precision=4 setting to the Julia/Newton formula in Standard.ufm because it turns out they need a little more precision than Mandelbrot-type formulas. Otherwise the calculation doesn't go to extended or arbitrary precision mode as needed when zooming in.

Fixed a bug that could cause far too many vertical strips to be created in the fractal window when using a high number of calculation threads in combination with certain image widths.

Fixed a bug that caused accented letters (e.g. for the author name or in the comments field) to be saved incorrectly on Mac.

Fixed a bug that caused the log function to return NAN when used with a large number (> 1e308) in arbitrary precision mode.

Fixed a bug that could cause a crash in the Modified Perlin Texture trap shape in reb.ulb.

Small bug fixes and improvements.


* What’s new in Ultra Fractal 6.02?

The toolbars for fractal windows, browser and formula editors can now be customized on Windows. Right-click a toolbar to select which buttons and other items should be shown. There are more actions available than before such as undo, redo, copy, paste, and the toolbar can now also be displayed in Small Icons mode so it becomes similar to the toolbar in Ultra Fractal 5. On Mac, the toolbar was already customizable, but the new actions are available here as well.

Fixed a problem that caused multithreading to work inefficiently in arbitrary precision mode with formulas that use classes/plug-ins.

Fixed a bug in the formula compiler that could cause some formulas that use the round/trunc/ceil/floor functions to produce a different image than in Ultra Fractal 5.

Fixed a bug that caused exported images in TIFF format to be unreadable in some programs.

Fixed a bug on Mac that could cause crashes when using a MacBook Pro with a pressure-sensitive trackpad.

Fixed a bug on Mac that would cause a crash when sorting an empty list in e.g. the Find Entries dialog in the browser.

Fixed a bug on Mac that caused the histogram in the Statistics tool window to be invisible.

Fixed a bug on Windows where the keyboard focus would be lost after showing an Open or Save dialog.

Fixed a bug on Windows where the tool windows would be shown incorrectly after clicking the Show Desktop button in task bar to hide all windows, and then activating another application.

Fixed a problem where the fractal window could become too small when slowly typing a new width or height value with the "Resize with fractal window" option enabled.

Small bug fixes and improvements.


* What's new in Ultra Fractal 6.01?

Updated the render to disk code to limit the amount of memory used while rendering, which also affects the size of temporary files and render backup jobs (*.URJ files).

Fixed a bug in the formula compiler that could cause the bailout condition of a formula to work incorrectly in arbitrary precision mode (when not using perturbation calculations).

Fixed a crash on Mac when restoring the position of a fractal window (e.g. when opening a previously opened fractal) that causes it to move to a different monitor.

Fixed a bug that caused the fractal to recalculate when minimizing and then restoring a maximized fractal window on Windows.

Fixed strange behavior when changing the size of a fractal in a maximized fractal window on Windows with the Resize with Window option enabled.

Added Ctrl+L and Ctrl+A shortcuts (Cmd+L and Cmd+A on Mac) to the gradient editor and made sure the gradient editor gets the focus when clicking in a curve if it is docked to a fractal window, so keyboard shortcuts actually work. Added Shift+Ctrl+E shortcut for the eyedropper.

Fixed a bug that could cause the save confirmation dialog to disappear behind another document window on Windows, making the program appear to be unresponsive.

Fixed a bug that caused the eyedropper/explore icons to not show up beneath input boxes in floating tool windows.

Fixed a bug that caused a crash when creating a docked Timeline tool window on a High DPI system on Windows.

Fixed a crash on Mac when pressing Cmd+N with no document windows open.

Fixed crashes on Windows when using OpenGL acceleration with unstable graphics drivers: in this case OpenGL acceleration is now automatically disabled.

Fixed a bug on Mac that caused dragging of e.g. the selection box in the fractal window to not work at all on MacBook Pros with pressure-sensitive trackpads.

Fixed bug that caused the Shift+F9/F10 shortcuts for the tool windows not to work.

Fixed a possible crash when switching between tabs in the Layer Properties tool window after deleting a layer or closing a fractal.

Fixed a bug that caused incorrect keyboard behavior in the Find Entries window.

Small bug fixes and improvements.


* What's new in Ultra Fractal 6?

Ultra Fractal 6 contains many new features: perturbation calculations for super-fast deep zooming, 64-bit support, Retina/High DPI support, OpenGL acceleration, anti-aliasing in the fractal window, render to disk improvements, a modernized interface on Windows, and much more. See the What's New chapter in the help file for more information.


* System requirements

On Windows, Ultra Fractal requires Windows XP or higher and runs best on Windows 10. On Mac, Ultra Fractal requires an Intel Mac and at least OS X 10.8, but preferably macOS 10.12 (Sierra) or higher.


* Installing Ultra Fractal

On Windows, double-click the installation program that you have downloaded. You cannot install Ultra Fractal 6 on top of an earlier version of Ultra Fractal. You must install Ultra Fractal 6 into its own folder. Just follow the instructions given by the Setup program.

On Mac, simply drag it from the downloaded disk image to the Applications folder on your Mac. To start it, click the Spotlight search icon at the top-right end of the menu bar, type 'Ultra Fractal' and click the application icon that appears. Alternatively, you can locate it in the Applications folder, use the Launcher, or pin it to the Dock so the icon is always available.
  
If you want to install multiple versions of Ultra Fractal on the same computer, it is recommended to install the earliest version first, and then later versions. For example, first install Ultra Fractal 5, and then Ultra Fractal 6. You can always download earlier versions by following the Previous versions link in the download section of the Ultra Fractal web site at www.ultrafractal.com/download.


* Getting started

When Ultra Fractal starts for the first time, it will automatically display a welcome dialog with links to important sections of the help file, such as What's New and Tutorials. Click on one of the topics to get started. If you are new to Ultra Fractal, the tutorials are highly recommended.


* Purchasing Ultra Fractal

You have downloaded an evaluation copy of Ultra Fractal 6. Click Information on the Purchase menu for more information on purchasing Ultra Fractal, or go to the Ultra Fractal web site: www.ultrafractal.com/shop


* Forum

There is a forum for discussing Ultra Fractal, asking questions, and exchanging parameter sets with other users. See www.ultrafractal.com/forum.


* Contacting the author

email:     info@ultrafractal.com
www:       www.ultrafractal.com

See also "support" in the help index.

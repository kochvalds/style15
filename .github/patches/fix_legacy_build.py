from pathlib import Path

root = Path(".")
private = root / "Source/Private.h"
text = private.read_text()
declarations = """
// Concrete UIKit base classes for Logos hooks.
@interface SBIconImageView : UIView @end
@interface SBFolderIconImageView : UIView @end
@interface SBIconView : UIView @end
@interface SBIconBadgeView : UIView @end
@interface SBDockView : UIView @end
@interface SBIconPageControl : UIView @end
@interface SBAwayView : UIView @end
@interface UIStatusBar : UIView @end
@interface SBIconLabelImageParameters : NSObject @end
@interface BBServer : NSObject @end

"""
if "@interface SBIconImageView : UIView" not in text:
    text = text.replace("// Утилиты из Core.xm", declarations + "// Утилиты из Core.xm")
    private.write_text(text)

core = root / "Source/Core.xm"
text = core.read_text()
text = text.replace("#import <AVFoundation/AVFoundation.h>\n", "")
start = text.index("void S15Torch(void) {")
end = text.index("\n}\n", start) + 2
torch = r'''void S15Torch(void) {
    // Runtime lookup avoids importing modern AVFoundation/simd headers
    // when building legacy armv7 targets with Theos toolchains.
    Class deviceClass = NSClassFromString(@"AVCaptureDevice");
    SEL defaultSel = NSSelectorFromString(@"defaultDeviceWithMediaType:");
    if (!deviceClass || ![deviceClass respondsToSelector:defaultSel]) return;
    id device = ((id (*)(id, SEL, id))objc_msgSend)(deviceClass, defaultSel, @"vide");
    if (!device) return;
    SEL hasTorchSel = NSSelectorFromString(@"hasTorch");
    SEL lockSel = NSSelectorFromString(@"lockForConfiguration:");
    SEL modeSel = NSSelectorFromString(@"torchMode");
    SEL setModeSel = NSSelectorFromString(@"setTorchMode:");
    SEL unlockSel = NSSelectorFromString(@"unlockForConfiguration");
    if (![device respondsToSelector:hasTorchSel] ||
        !((BOOL (*)(id, SEL))objc_msgSend)(device, hasTorchSel)) return;
    if (![device respondsToSelector:lockSel] ||
        !((BOOL (*)(id, SEL, id))objc_msgSend)(device, lockSel, nil)) return;
    NSInteger mode = ((NSInteger (*)(id, SEL))objc_msgSend)(device, modeSel);
    ((void (*)(id, SEL, NSInteger))objc_msgSend)(device, setModeSel, mode == 1 ? 0 : 1);
    ((void (*)(id, SEL))objc_msgSend)(device, unlockSel);
}'''
if "AVCaptureDevice *d =" in text:
    text = text[:start] + torch + text[end:]
core.write_text(text)

makefile = root / "Makefile"
text = makefile.read_text().replace("TARGET = iphone:clang:latest:4.3", "TARGET = iphone:clang:latest:6.0")
text = text.replace("UIKit QuartzCore CoreGraphics AVFoundation", "UIKit QuartzCore CoreGraphics")
if "-Wno-error=arc-performSelector-leaks" not in text:
    text = text.replace("Style15_CFLAGS = ", "Style15_CFLAGS = -Wno-error=arc-performSelector-leaks ")
makefile.write_text(text)

# Modern UIKit SDK renamed these legacy enum constants.
for source in (root / "Source").glob("*.xm"):
    source_text = source.read_text()
    replacements = {
        "UITextAlignmentLeft": "NSTextAlignmentLeft",
        "UITextAlignmentCenter": "NSTextAlignmentCenter",
        "UITextAlignmentRight": "NSTextAlignmentRight",
        "UITextAlignmentJustified": "NSTextAlignmentJustified",
        "UITextAlignmentNatural": "NSTextAlignmentNatural",
        "UILineBreakModeWordWrap": "NSLineBreakByWordWrapping",
        "UILineBreakModeCharacterWrap": "NSLineBreakByCharWrapping",
        "UILineBreakModeClip": "NSLineBreakByClipping",
        "UILineBreakModeHeadTruncation": "NSLineBreakByTruncatingHead",
        "UILineBreakModeTailTruncation": "NSLineBreakByTruncatingTail",
        "UILineBreakModeMiddleTruncation": "NSLineBreakByTruncatingMiddle",
    }
    for old, new in replacements.items():
        source_text = source_text.replace(old, new)
    source.write_text(source_text)

print("Applied legacy SDK/source compatibility fixes.")

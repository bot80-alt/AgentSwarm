import { cn } from "@/lib/utils";
import { forwardRef, type HTMLAttributes } from "react";

export const BaseNode = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        "relative rounded-lg border border-border bg-card text-card-foreground shadow-sm",
        "hover:shadow-md transition-shadow",
        className,
      )}
      {...props}
    />
  ),
);
BaseNode.displayName = "BaseNode";

export const BaseNodeHeader = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn("flex items-center gap-2 border-b border-border px-3 py-2", className)} {...props} />
  ),
);
BaseNodeHeader.displayName = "BaseNodeHeader";

export const BaseNodeContent = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => <div ref={ref} className={cn("px-3 py-2", className)} {...props} />,
);
BaseNodeContent.displayName = "BaseNodeContent";

export const BaseNodeFooter = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn("border-t border-border px-3 py-1.5 text-xs text-muted-foreground", className)} {...props} />
  ),
);
BaseNodeFooter.displayName = "BaseNodeFooter";

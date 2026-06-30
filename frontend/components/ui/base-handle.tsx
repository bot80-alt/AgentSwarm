import { Handle, type HandleProps } from "@xyflow/react";
import { forwardRef } from "react";

import { cn } from "@/lib/utils";

export type BaseHandleProps = HandleProps;

export const BaseHandle = forwardRef<HTMLDivElement, BaseHandleProps>(
  ({ className, ...props }, ref) => (
    <Handle
      ref={ref}
      className={cn(
        "!h-2.5 !w-2.5 !border-2 !border-border !bg-muted-foreground/50",
        className,
      )}
      {...props}
    />
  ),
);
BaseHandle.displayName = "BaseHandle";

import toast from "react-hot-toast";

export function displaySuccessToast(message: string): void {
  toast.success(message);
}

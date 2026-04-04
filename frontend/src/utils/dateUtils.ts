import { formatDistanceToNow, format, differenceInHours } from "date-fns";

export const formatDeadline = (deadline: string) =>
  format(new Date(deadline), "dd MMM yyyy, h:mm a");

export const deadlineUrgency = (deadline: string): "red" | "orange" | "green" => {
  const hours = differenceInHours(new Date(deadline), new Date());
  if (hours < 0) return "red";
  if (hours < 24) return "red";
  if (hours < 72) return "orange";
  return "green";
};

export const timeAgo = (date: string) =>
  formatDistanceToNow(new Date(date), { addSuffix: true });

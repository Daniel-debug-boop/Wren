import { useEffect, useRef, useState } from "react";
import { io, Socket } from "socket.io-client";

interface StreamChunk {
  type: "token" | "status" | "memory" | "timeline";
  data: unknown;
}

export function useSocket(conversationId: string | null) {
  const socketRef = useRef<Socket | null>(null);
  const [connected, setConnected] = useState(false);
  const [chunks, setChunks] = useState<StreamChunk[]>([]);

  useEffect(() => {
    if (!conversationId) return () => {};
    const socket = io("/", { path: "/ws", query: { conversationId } });
    socketRef.current = socket;
    socket.on("connect", () => setConnected(true));
    socket.on("disconnect", () => setConnected(false));
    socket.on("message", (chunk: StreamChunk) =>
      setChunks((c) => [...c, chunk]),
    );
    return () => {
      socket.disconnect();
      socketRef.current = null;
    };
  }, [conversationId]);

  return { socket: socketRef, connected, chunks };
}

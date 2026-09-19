export class ApiError extends Error {
  constructor(
    message: string,
    public code: string,
  ) {
    super(message);
  }
}
export async function api<T>(
  path: string,
  method = "GET",
  body?: unknown,
): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`/api${path}`, {
      method,
      headers:
        body === undefined ? undefined : { "Content-Type": "application/json" },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch {
    throw new ApiError(
      "Não foi possível conectar. Verifique se o sistema está disponível e tente novamente.",
      "NETWORK_ERROR",
    );
  }
  const payload = await response.json().catch(() => null);
  if (!response.ok)
    throw new ApiError(
      payload?.error?.message ?? "Não foi possível concluir. Tente novamente.",
      payload?.error?.code ?? "UNKNOWN_ERROR",
    );
  if (!payload || !("data" in payload))
    throw new ApiError(
      "O sistema retornou uma resposta inesperada. Tente novamente.",
      "INVALID_RESPONSE",
    );
  return payload.data as T;
}

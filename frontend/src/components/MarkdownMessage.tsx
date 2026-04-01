import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

type Props = {
  content: string;
  className?: string;
};

export default function MarkdownMessage({ content, className }: Props) {
  return (
    <div className={["break-words text-[15px] leading-6 text-white", className].filter(Boolean).join(' ')}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          h1: ({ children }) => (
            <h1 className="mb-2 text-lg font-bold sm:text-xl">{children}</h1>
          ),
          h2: ({ children }) => (
            <h2 className="mb-1.5 text-base font-semibold sm:text-lg">{children}</h2>
          ),
          h3: ({ children }) => (
            <h3 className="mb-1.5 text-[15px] font-semibold sm:text-base">{children}</h3>
          ),
          p: ({ children }) => (
            <p className="mb-1.5 text-[15px] leading-6 last:mb-0">{children}</p>
          ),
          ul: ({ children }) => (
            <ul className="mb-1.5 list-disc space-y-1 pl-5 text-[15px]">{children}</ul>
          ),
          ol: ({ children }) => (
            <ol className="mb-2 list-decimal space-y-1 pl-5 text-[15px]">{children}</ol>
          ),
          li: ({ children }) => (
            <li className="leading-6">{children}</li>
          ),
          strong: ({ children }) => (
            <strong className="font-semibold">{children}</strong>
          ),
          a: ({ href, children }) => (
            <a
              href={href}
              target="_blank"
              rel="noreferrer"
              className="underline underline-offset-2"
            >
              {children}
            </a>
          ),
          code: ({ children }) => (
            <code className="rounded bg-black/10 px-1 py-0.5 text-[0.92em]">
              {children}
            </code>
          ),
          pre: ({ children }) => (
            <pre className="mb-2 overflow-x-auto rounded-xl bg-black/10 p-3 text-sm leading-6">
              {children}
            </pre>
          ),
          blockquote: ({ children }) => (
            <blockquote className="mb-2 border-l-4 border-white/40 pl-3 italic">
              {children}
            </blockquote>
          ),
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
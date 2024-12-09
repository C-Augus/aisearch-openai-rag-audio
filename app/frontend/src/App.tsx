import { useState, useEffect } from "react";
import { Mic, MicOff } from "lucide-react";
// import { useTranslation } from "react-i18next";

import { Button } from "@/components/ui/button";
import { GroundingFiles } from "@/components/ui/grounding-files";
import { InterviewAnswers } from "./components/ui/interview-answers";
import GroundingFileView from "@/components/ui/grounding-file-view";
import StatusMessage from "@/components/ui/status-message";

import useRealTime from "@/hooks/useRealtime";
import useAudioRecorder from "@/hooks/useAudioRecorder";
import useAudioPlayer from "@/hooks/useAudioPlayer";

import { GroundingFile, InterviewItem, ToolResult } from "./types";

import logo from "./assets/logo.svg";
import pentareLogo from "./assets/pentare_logo.png";
import microsoftLogo from "./assets/microsoft_logo.png";

function App() {
    const [isRecording, setIsRecording] = useState(false);
    const [groundingFiles, setGroundingFiles] = useState<GroundingFile[]>([]);
    const [selectedFile, setSelectedFile] = useState<GroundingFile | null>(null);
    const [interviewDetected, setInterviewDetected] = useState<boolean>(false);
    const [interviewAnswers, setInterviewAnswers] = useState<InterviewItem>();
    const [interviewStep, setInterviewStep] = useState<number>(0);
    const [isValidanting, setIsValidating] = useState<boolean>(false);

    const { startSession, addUserAudio, inputAudioBufferClear } = useRealTime({
        enableInputAudioTranscription: true,
        onReceivedInputAudioTranscriptionCompleted: message => { // Sender
            if (interviewDetected && !isValidanting) {
               switch(interviewStep) {
                    case 0:
                        setInterviewAnswers({
                            ...interviewAnswers,
                            name: message.transcript?.replace(/[\n.]/g, "") || "Não obtido",
                        });
                        break;
                    case 1:
                        if (interviewAnswers) {
                            setInterviewAnswers({
                                ...interviewAnswers,
                                cpf: message.transcript?.match(/\d+/g)?.join('') || "Não obtido",
                            });
                        };
                        break;
                    case 2:
                        if (interviewAnswers) {
                            setInterviewAnswers({
                                ...interviewAnswers,
                                expirationDate: message.transcript?.replace(/[\n.]/g, "") || "Não obtido",
                            });
                        };
                        break;
                    case 3:
                        if (interviewAnswers) {
                            setInterviewAnswers({
                                ...interviewAnswers,
                                category: message.transcript?.replace(/[\n.]/g, "") || "Não obtido",
                            });
                        };
                        break;
                    case 4:
                        setInterviewDetected(false);
                        setInterviewAnswers({ name: "", cpf: "", expirationDate: "", category: "" });
                    }                
            }
        },
        onReceivedResponseDone: message => { // Assistant
            const transcript = message.response.output.map(output => output.content?.map(content => content.transcript).join(" ")).join(" ");

            if (!transcript) {
                return;
            }
            
            setIsValidating(false);

            if (transcript.includes("correto"))
                setIsValidating(true);

            if (transcript.includes("nome completo")) {
                setInterviewDetected(true);
                setInterviewStep(0)
            } else if (transcript.includes("seu CPF")) {
                setInterviewStep(1)
            } else if (transcript.includes("data de expiração") || transcript.includes("data de validade")) {
                setInterviewStep(2)
            } else if (transcript.includes("categoria")) {
                setInterviewStep(3)
            } else if (transcript.includes("sucesso")) {
                setInterviewStep(4);
            }     
        },
        onWebSocketOpen: () => console.log("WebSocket connection opened"),
        onWebSocketClose: () => console.log("WebSocket connection closed"),
        onWebSocketError: event => console.error("WebSocket error:", event),
        onReceivedError: message => console.error("error", message),
        onReceivedResponseAudioDelta: message => {
            isRecording && playAudio(message.delta);
        },
        onReceivedInputAudioBufferSpeechStarted: () => {
            stopAudioPlayer();
        },
        onReceivedExtensionMiddleTierToolResponse: message => {
            const result: ToolResult = JSON.parse(message.tool_result);

            const files: GroundingFile[] = result.sources.map(x => {
                return { id: x.chunk_id, name: x.title, content: x.chunk };
            });

            setGroundingFiles(prev => [...prev, ...files]);
        }
    });

    const { reset: resetAudioPlayer, play: playAudio, stop: stopAudioPlayer } = useAudioPlayer();
    const { start: startAudioRecording, stop: stopAudioRecording } = useAudioRecorder({ onAudioRecorded: addUserAudio });

    const onToggleListening = async () => {
        if (!isRecording) {
            startSession();
            await startAudioRecording();
            resetAudioPlayer();

            setIsRecording(true);
        } else {
            await stopAudioRecording();
            stopAudioPlayer();
            inputAudioBufferClear();

            setIsRecording(false);
        }
    };

    // const { t } = useTranslation();

    useEffect(() => {
        console.log("interviewDected: ",interviewDetected);
        console.log("interviewAnswers: ",interviewAnswers);
        console.log("interviewStep: ",interviewStep);
        console.log("isValidating: ",isValidanting);
    }, [interviewDetected, interviewAnswers, interviewStep, isValidanting])

    return (
        <div className="flex min-h-screen flex-col bg-gray-100 text-gray-900">
            <div className="p-4 sm:absolute sm:left-4 sm:top-4">
                <img src={logo} alt="Azure logo" className="h-16 w-16" />
            </div>
            <main className="flex flex-grow flex-col items-center justify-center">
                <h1 className="mb-8 bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-4xl font-bold text-transparent md:text-7xl">
                    Fale com os seus dados
                </h1>
                <div className="mb-4 flex flex-col items-center justify-center">
                    <Button
                        onClick={onToggleListening}
                        className={`h-12 w-60 ${isRecording ? "bg-red-600 hover:bg-red-700" : "bg-purple-500 hover:bg-purple-600"}`}
                        aria-label={isRecording ? "Parar gravação" : "Começar gravação"}
                    >
                        {isRecording ? (
                            <>
                                <MicOff className="mr-2 h-4 w-4" />
                                Parar conversa
                            </>
                        ) : (
                            <>
                                <Mic className="mr-2 h-6 w-6" />
                            </>
                        )}
                    </Button>
                    <StatusMessage isRecording={isRecording} />
                </div>
                <GroundingFiles files={groundingFiles} onSelected={setSelectedFile} />
                <InterviewAnswers answers={interviewAnswers} />
            </main>

            <footer className="flex flex-col py-4 text-center place-items-center gap-4 text-slate-500">
                <p>Uma parceria</p>
                <div className="flex flex-row gap-10 items-center bg-white w-fit rounded-2xl p-6 shadow-lg border-stone-[150] border-[1px]">
                    <img src={pentareLogo} alt="Microsoft logo" className="h-16" />
                    <img src={microsoftLogo} alt="Pentare logo" className="h-10" />
                </div>
                <p>Criado com Azure AI Search + Azure OpenAI</p>
            </footer>

            <GroundingFileView groundingFile={selectedFile} onClosed={() => setSelectedFile(null)} />
        </div>
    );
}

export default App;

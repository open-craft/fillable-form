import { ActionRow, Button, Card, Icon, Stack } from "@openedx/paragon";
import { Download, InfoOutline } from "@openedx/paragon/icons";
import { FormattedMessage } from "react-intl";
import { learnerMessages } from "../common/messages";

export interface DownloadButtonProps {
  downloadUrl: string;
  downloadButtonInfo: string;
};

export const DownloadButton = ({
  downloadUrl,
  downloadButtonInfo
}: DownloadButtonProps) => (
  <Card orientation='horizontal' className='p-2'>
    <Card.Section >
      <Stack direction="horizontal" gap={3}>
        <Icon src={InfoOutline} />
        <span>
          {downloadButtonInfo ? (
            downloadButtonInfo
          ) : (
            <FormattedMessage {...learnerMessages.downloadButtonInfoDefault} />
          )}  
        </span>
      </Stack>
    </Card.Section>
    <Card.Footer>
      <ActionRow>
        <Button
          as="a"
          href={downloadUrl}
          target="_blank"
          variant="tertiary"
          iconAfter={Download}
        >
          <FormattedMessage {...learnerMessages.downloadButton} />
        </Button>
      </ActionRow>
    </Card.Footer> 
  </Card>
);

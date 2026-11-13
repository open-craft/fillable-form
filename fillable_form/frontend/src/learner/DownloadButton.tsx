import { ActionRow, Button, Card, Icon, Stack } from "@openedx/paragon";
import { Download, InfoOutline } from "@openedx/paragon/icons";
import { FormattedMessage } from "react-intl";
import { learnerMessages } from "../common/messages";

export const DownloadButton = ({ downloadUrl }: { downloadUrl: string }) => {
  return (
    <Card orientation='horizontal' className='p-2'>
      <Card.Section >
        <Stack direction="horizontal" gap={3}>
          <Icon src={InfoOutline} />
          <span>Save your journal entries from this course as a single PDF and see how your perspective changed.</span>
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
};
